class DomainError(Exception):
    """Base class for expected domain failures."""


class DisruptionDriverMismatchError(DomainError):
    """Raised when a disruption is applied to a different driver."""


class PlanReferenceError(DomainError):
    """Raised when a plan references an unknown driver or load."""
