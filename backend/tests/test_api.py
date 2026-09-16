from fastapi.testclient import TestClient

from app.main import app, create_app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_local_frontend_origin_is_allowed_by_cors() -> None:
    response = client.options(
        "/api/demo/plan",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_production_frontend_origin_is_allowed_by_cors() -> None:
    response = client.options(
        "/api/demo/plan",
        headers={
            "Origin": "https://dispatchdiff.vercel.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://dispatchdiff.vercel.app"


def test_configured_frontend_origin_is_allowed_by_cors(monkeypatch) -> None:
    monkeypatch.setenv("FRONTEND_ORIGIN", "https://dispatchdiff-preview.vercel.app/")
    configured_client = TestClient(create_app())
    response = configured_client.options(
        "/api/demo/plan",
        headers={
            "Origin": "https://dispatchdiff-preview.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://dispatchdiff-preview.vercel.app"
    )


def test_unrelated_origin_is_not_allowed_by_cors() -> None:
    response = client.options(
        "/api/demo/plan",
        headers={
            "Origin": "https://unrelated.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_drivers_endpoint() -> None:
    response = client.get("/api/demo/drivers")
    assert response.status_code == 200
    assert len(response.json()) == 8


def test_loads_endpoint() -> None:
    response = client.get("/api/demo/loads")
    assert response.status_code == 200
    assert len(response.json()) == 12


def test_plan_endpoint() -> None:
    response = client.get("/api/demo/plan")
    assert response.status_code == 200
    body = response.json()
    assert body["plan"]["assignments"]
    assert body["unassigned_load_ids"]
    assert body["evaluation_summary"]["total_loads"] == 12


def test_successful_evaluation_endpoint() -> None:
    response = client.post("/api/evaluate", json={"driver_id": "DRV-001", "load_id": "LOAD-001"})
    assert response.status_code == 200
    body = response.json()
    assert body["feasible"] is True
    assert body["score"] == 1812.5
    assert body["violations"] == []


def test_infeasible_evaluation_endpoint() -> None:
    response = client.post("/api/evaluate", json={"driver_id": "DRV-007", "load_id": "LOAD-011"})
    assert response.status_code == 200
    body = response.json()
    assert body["feasible"] is False
    assert body["score"] is None
    assert body["planned_pickup_at"] is not None
    assert "HOS_INSUFFICIENT" in {item["code"] for item in body["violations"]}


def test_unknown_driver_returns_404() -> None:
    response = client.post("/api/evaluate", json={"driver_id": "missing", "load_id": "LOAD-001"})
    assert response.status_code == 404


def test_unknown_load_returns_404() -> None:
    response = client.post("/api/evaluate", json={"driver_id": "DRV-001", "load_id": "missing"})
    assert response.status_code == 404


def test_demo_disruption_endpoint() -> None:
    response = client.get("/api/demo/disruption")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "DRIVER_DETENTION"
    assert body["detention_minutes"] == 180


def test_demo_replan_returns_complete_structured_result() -> None:
    response = client.post("/api/demo/replan")
    assert response.status_code == 200
    body = response.json()
    assert body["previous_plan"]["assignments"]
    assert body["proposed_plan"]["assignments"]
    assert len(body["preserved_assignments"]) == 4
    assert body["removed_assignments"]
    assert body["added_assignments"]
    assert {item["change_type"] for item in body["assignment_changes"]} == {
        "PRESERVED",
        "REMOVED",
        "ADDED",
    }
    assert set(body["metrics"]) == {"before_metrics", "after_metrics", "delta"}


def test_replan_accepts_valid_disruption() -> None:
    disruption = client.get("/api/demo/disruption").json()
    response = client.post("/api/replan", json={"disruption": disruption})
    assert response.status_code == 200
    assert response.json()["impacted_assignments"][0]["load_id"] == "LOAD-001"


def test_replan_unknown_driver_returns_404() -> None:
    disruption = client.get("/api/demo/disruption").json()
    disruption["driver_id"] = "DRV-MISSING"
    response = client.post("/api/replan", json={"disruption": disruption})
    assert response.status_code == 404


def test_replan_malformed_disruption_returns_422() -> None:
    disruption = client.get("/api/demo/disruption").json()
    disruption["detention_minutes"] = 0
    response = client.post("/api/replan", json={"disruption": disruption})
    assert response.status_code == 422
