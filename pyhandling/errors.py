__all__ = (
    "PyhandingError",
    "ArgumentError",
    "ReturningError",
    "InvalidInitializationError",
    "AtomizationError",
    "TemplatedActionChainError",
    "ActionCursorError",
)


class PyhandingError(Exception):
    ...


class ArgumentError(PyhandingError):
    ...


class FlagError(PyhandingError):
    ...


class ReturningError(PyhandingError):
    ...


class InvalidInitializationError(PyhandingError):
    ...


class AtomizationError(PyhandingError):
    ...


class ActionChainError(PyhandingError):
    ...


class TemplatedActionChainError(ActionChainError):
    __notes__ = ["Regular chain should not contain Ellipsis"]


class ActionCursorError(PyhandingError):
    ...
