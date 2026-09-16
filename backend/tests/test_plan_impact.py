from app.disruptions.service import apply_disruption
from app.domain.enums import ConstraintViolationCode
from app.planning.service import PlanningService
from app.replanning.impact import evaluate_plan_impact
from app.seed.demo_data import DEMO_DRIVERS, DEMO_LOADS, get_demo_disruption


def disrupted_fleet():
    disruption = get_demo_disruption()
    return tuple(
        apply_disruption(driver, disruption) if driver.id == disruption.driver_id else driver
        for driver in DEMO_DRIVERS
    )


def test_disruption_invalidates_expected_assignment_and_preserves_reason() -> None:
    plan = PlanningService().build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS).plan
    impacts = evaluate_plan_impact(plan, disrupted_fleet(), DEMO_LOADS)
    target = next(impact for impact in impacts if impact.load_id == "LOAD-001")
    assert target.impacted is True
    assert [reason.code for reason in target.reasons] == [
        ConstraintViolationCode.PICKUP_WINDOW_MISSED
    ]


def test_unaffected_assignments_stay_unaffected() -> None:
    plan = PlanningService().build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS).plan
    impacts = evaluate_plan_impact(plan, disrupted_fleet(), DEMO_LOADS)
    unaffected = [impact for impact in impacts if not impact.impacted]
    assert len(unaffected) == 4
    assert all(not impact.reasons for impact in unaffected)
