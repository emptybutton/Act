__all__ = (
    "ActError",
    "ArgumentError",
    "ReturningError",
    "UniaError",
    "InvalidInitializationError",
    "AtomizationError",
    "MatchingError",
    "TemplatedActionChainError",
    "ObjectTemplateError",
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


class ObjectTemplateError(ActError):
    ...


class ActionCursorError(ActError):
    ...


class StructureError(ActError):
    ...


class RangeConstructionError(StructureError, ValueError):
    ...


class IndexingError(StructureError, IndexError):
    ...
