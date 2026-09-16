from app.domain.models import Load


def calculate_assignment_score(load: Load, deadhead_minutes: int) -> float:
    if deadhead_minutes < 0:
        raise ValueError("deadhead_minutes cannot be negative")
    revenue_dollars = load.revenue_cents / 100
    return round(revenue_dollars - (deadhead_minutes * 1.25), 2)
