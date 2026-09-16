from dataclasses import replace

from app.planning.scoring import calculate_assignment_score
from app.seed.demo_data import DEMO_LOADS


def test_exact_scoring_formula() -> None:
    assert calculate_assignment_score(DEMO_LOADS[0], 30) == 1812.50


def test_higher_deadhead_lowers_score() -> None:
    assert calculate_assignment_score(DEMO_LOADS[0], 60) < calculate_assignment_score(
        DEMO_LOADS[0], 30
    )


def test_money_conversion_uses_cents() -> None:
    load = replace(DEMO_LOADS[0], revenue_cents=12345)
    assert calculate_assignment_score(load, 0) == 123.45
