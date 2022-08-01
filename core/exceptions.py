"""Some general exception classes used throughout the program."""


class MissingDependencyError(RuntimeError):
    """Raised if a required system dependency is missing."""

    pass
