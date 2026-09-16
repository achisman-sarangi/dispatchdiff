from app.planning.service import PlanningService
from app.replanning.metrics import calculate_metric_delta, calculate_plan_metrics
from app.replanning.service import ReplanningService
from app.seed.demo_data import DEMO_DRIVERS, DEMO_LOADS, get_demo_disruption


def demo_result():
    planning = PlanningService()
    plan = planning.build_greedy_plan(DEMO_DRIVERS, DEMO_LOADS).plan
    return ReplanningService(planning).replan_after_disruption(
        DEMO_DRIVERS, DEMO_LOADS, plan, get_demo_disruption()
    )


def test_before_and_after_metrics_are_calculated_from_plans() -> None:
    result = demo_result()
    before = result.metrics.before_metrics
    after = result.metrics.after_metrics
    assert before.assigned_loads == len(result.previous_plan.assignments) == 5
    assert after.assigned_loads == len(result.proposed_plan.assignments) == 6
    assert before.unassigned_loads == 7
    assert after.unassigned_loads == 6
    assert before.committed_loads_unassigned == 0
    assert after.committed_loads_unassigned == 0


def test_revenue_and_deadhead_come_from_assignments() -> None:
    result = demo_result()
    loads = {load.id: load for load in DEMO_LOADS}
    expected_revenue = sum(
        loads[assignment.load_id].revenue_cents for assignment in result.proposed_plan.assignments
    )
    assert result.metrics.after_metrics.total_revenue_cents == expected_revenue
    assert result.metrics.after_metrics.total_deadhead_minutes == sum(
        assignment.deadhead_minutes for assignment in result.proposed_plan.assignments
    )


def test_delta_is_after_minus_before() -> None:
    result = demo_result()
    before = result.metrics.before_metrics
    after = result.metrics.after_metrics
    assert result.metrics.delta == calculate_metric_delta(before, after)
    assert result.metrics.delta.revenue_cents_delta == 190000
    assert result.metrics.delta.deadhead_minutes_delta == 30
    assert result.metrics.delta.changed_assignments == 3


def test_committed_unassigned_and_violation_counts() -> None:
    result = demo_result()
    metrics = calculate_plan_metrics(
        result.proposed_plan, DEMO_DRIVERS, DEMO_LOADS, changed_assignments=3
    )
    assert metrics.committed_loads_unassigned == 0
    assert result.metrics.after_metrics.hos_violations == 0
    assert result.metrics.after_metrics.late_loads == 0
