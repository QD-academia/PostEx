class PostExError(Exception):
    """Base exception."""


class ApprovalRequired(PostExError):
    """An action was attempted without a current approval."""


class LockViolation(PostExError):
    """A proposed mutation targets an explicitly locked design element."""


class InvalidTransition(PostExError):
    """A state transition violated workflow sequencing."""


class ConfigurationError(PostExError):
    """Configuration or an optional runtime dependency is invalid."""


class EvidenceError(PostExError):
    """Evidence coverage or linkage is invalid."""
