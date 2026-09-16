from app.domain.enums import AssignmentChangeType, ConstraintViolationCode
from app.planning.service import PlanningService
from app.replanning.service import ReplanningService
from app.seed.demo_data import DEMO_DRIVERS, DEMO_LOADS, get_demo_disruption


def build_result():
    planning = PlanningService()
    plan = planning.build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS).plan
    return ReplanningService(planning).replan_after_disruption(
        DEMO_DRIVERS, DEMO_LOADS, plan, get_demo_disruption()
    )


def test_impacted_assignment_is_removed_and_load_is_reassigned() -> None:
    result = build_result()
    assert [(item.driver_id, item.load_id) for item in result.removed_assignments] == [
        ("DRV-001", "LOAD-001")
    ]
    assert ("DRV-007", "LOAD-001") in {
        (item.driver_id, item.load_id) for item in result.added_assignments
    }


def test_unaffected_assignments_are_preserved_exactly() -> None:
    result = build_result()
    previous_by_load = {item.load_id: item for item in result.previous_plan.assignments}
    assert len(result.preserved_assignments) == 4
    assert all(item is previous_by_load[item.load_id] for item in result.preserved_assignments)


def test_disrupted_driver_is_not_reused_for_invalidated_load() -> None:
    result = build_result()
    replacement = next(item for item in result.added_assignments if item.load_id == "LOAD-001")
    assert replacement.driver_id != get_demo_disruption().driver_id


def test_no_driver_receives_more_than_one_load_and_committed_recovery_is_first() -> None:
    result = build_result()
    driver_ids = [item.driver_id for item in result.proposed_plan.assignments]
    assert len(driver_ids) == len(set(driver_ids))
    assert result.added_assignments[0].load_id == "LOAD-001"


def test_repeated_runs_are_identical_and_seed_objects_are_unchanged() -> None:
    drivers_snapshot = tuple(DEMO_DRIVERS)
    loads_snapshot = tuple(DEMO_LOADS)
    first = build_result()
    second = build_result()
    assert first == second
    assert DEMO_DRIVERS == drivers_snapshot
    assert DEMO_LOADS == loads_snapshot


def test_still_unassignable_load_remains_unassigned() -> None:
    assert "LOAD-012" in build_result().still_unassigned_load_ids


def test_diff_contains_preserved_removed_and_added_with_actual_reason() -> None:
    changes = build_result().assignment_changes
    assert {change.change_type for change in changes} == set(AssignmentChangeType)
    removed = next(
        change for change in changes if change.change_type is AssignmentChangeType.REMOVED
    )
    replacement = next(
        change
        for change in changes
        if change.change_type is AssignmentChangeType.ADDED and change.load_id == "LOAD-001"
    )
    assert removed.reason_codes == (ConstraintViolationCode.PICKUP_WINDOW_MISSED,)
    assert "pickup window" in removed.explanation
    assert "180-minute detention" in replacement.explanation
    assert "PICKUP_WINDOW_MISSED" in replacement.explanation
    assert changes == build_result().assignment_changes
