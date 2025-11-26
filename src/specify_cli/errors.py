"""Exception hierarchy for Specify CLI."""


class SpecKitError(Exception):
    """Base exception for Spec Kit errors."""

    def __init__(self, message: str, exit_code: int = 1):
        self.message = message
        self.exit_code = exit_code
        super().__init__(self.message)


class ConfigError(SpecKitError):
    """Configuration related errors."""

    pass


class CliError(SpecKitError):
    """CLI usage errors."""

    pass


class ServiceError(SpecKitError):
    """External service errors."""

    pass
