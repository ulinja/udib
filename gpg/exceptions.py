"""Exceptions which may be raised during execution of gpg wrapper functions."""


class GpgProgrammingException(Exception):
    """A general exception indicating a programming error."""

    pass


class GpgRuntimeError(RuntimeError):
    """A general exception indicating a runtime error."""

    pass


class UnexpectedOutputException(GpgProgrammingException):
    """Raised when a gpg subprocess produces unexpected output."""

    pass


class MissingLocalKeyError(GpgRuntimeError):
    """Raised when an expected key is missing from the local keystore."""

    pass


class InvalidSignatureError(GpgRuntimeError):
    """Raised when an invalid gpg signature is encountered."""

    pass


class VerificationFailedError(GpgRuntimeError):
    """Raised when a gpg verfication encounters a bad signature."""

    pass
