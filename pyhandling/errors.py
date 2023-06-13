__all__ = (
    "PyhandingError",
    "ArgumentError",
    "ReturningError",
    "UniaError",
    "InvalidInitializationError",
    "AtomizationError",
    "MatchingError",
    "TemplatedActionChainError",
    "ActionCursorError",
    "StructureError",
    "RangeConstructionError"
)


class PyhandingError(Exception):
    ...


class ArgumentError(PyhandingError):
    ...


class FlagError(PyhandingError):
    ...


class ReturningError(PyhandingError):
    ...


class UniaError(PyhandingError):
    ...


class InvalidInitializationError(PyhandingError):
    ...


class AtomizationError(PyhandingError):
    ...


class MatchingError(PyhandingError):
    ...


class ActionChainError(PyhandingError):
    ...


class TemplatedActionChainError(ActionChainError):
    __notes__ = ["Regular chain should not contain `Ellipsis`"]


class ActionCursorError(PyhandingError):
    ...


class StructureError(PyhandingError):
    ...


class RangeConstructionError(StructureError, ValueError):
    ...
