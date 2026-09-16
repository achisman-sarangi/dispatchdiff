from dataclasses import replace

from app.domain.enums import DriverStatus
from app.planning.service import PlanningService
from app.seed.demo_data import DEMO_DRIVERS, DEMO_LOADS

service = PlanningService()


def test_ranking_excludes_infeasible_drivers() -> None:
    candidates = service.rank_feasible_drivers(DEMO_LOADS[0], DEMO_DRIVERS)
    candidate_ids = {candidate.driver.id for candidate in candidates}
    assert "DRV-006" not in candidate_ids
    assert "DRV-004" not in candidate_ids


def test_ranking_sorts_highest_score_first() -> None:
    high_revenue_load = replace(DEMO_LOADS[0], estimated_deadhead_minutes=10)
    low_deadhead_driver = DEMO_DRIVERS[0]
    candidates = service.rank_feasible_drivers(
        high_revenue_load, [low_deadhead_driver, DEMO_DRIVERS[2]]
    )
    assert candidates[0].score >= candidates[1].score


def test_ranking_uses_driver_id_as_deterministic_tie_breaker() -> None:
    driver_b = replace(DEMO_DRIVERS[0], id="DRV-B")
    driver_a = replace(DEMO_DRIVERS[0], id="DRV-A")
    candidates = service.rank_feasible_drivers(DEMO_LOADS[0], [driver_b, driver_a])
    assert [candidate.driver.id for candidate in candidates] == ["DRV-A", "DRV-B"]


def test_driver_is_assigned_at_most_once() -> None:
    driver = replace(DEMO_DRIVERS[0], status=DriverStatus.AVAILABLE)
    second_load = replace(DEMO_LOADS[0], id="LOAD-COPY")
    result = service.build_greedy_plan([driver], [DEMO_LOADS[0], second_load])
    assert len(result.plan.assignments) == 1
    assert len({item.driver_id for item in result.plan.assignments}) == 1


def test_unassignable_load_appears_in_result() -> None:
    result = service.build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS)
    assert "LOAD-012" in result.unassigned_load_ids


def test_evaluation_summary_matches_assignments() -> None:
    result = service.build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS)
    assigned_loads = {item.load_id for item in result.plan.assignments}
    expected_revenue = sum(load.revenue_cents for load in DEMO_LOADS if load.id in assigned_loads)
    assert result.evaluation_summary.total_loads == len(DEMO_LOADS)
    assert result.evaluation_summary.assigned_loads == len(result.plan.assignments)
    assert result.evaluation_summary.unassigned_loads == len(result.unassigned_load_ids)
    assert result.evaluation_summary.total_revenue_cents == expected_revenue
    assert result.evaluation_summary.total_deadhead_minutes == sum(
        item.deadhead_minutes for item in result.plan.assignments
    )
