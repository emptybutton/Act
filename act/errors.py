__all__ = (
    "ActError",
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


class ActError(Exception):
    ...


class ArgumentError(ActError):
    ...


class FlagError(ActError):
    ...


class ReturningError(ActError):
    ...


class UniaError(ActError):
    ...


class InvalidInitializationError(ActError):
    ...


class AtomizationError(ActError):
    ...


class MatchingError(ActError):
    ...


class ActionChainError(ActError):
    ...


class TemplatedActionChainError(ActionChainError):
    __notes__ = ["Regular chain should not contain `Ellipsis`"]


    ...


class ActionCursorError(ActError):
    ...


class StructureError(ActError):
    ...


class RangeConstructionError(StructureError, ValueError):
    ...


class IndexingError(StructureError, IndexError):
    ...
