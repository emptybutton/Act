__all__ = (
    "ActError",
    "ArgumentError",
    "ReturningError",
    "UnionError",
    "InvalidInitializationError",
    "AtomizationError",
    "MatchingError",
    "ObjectTemplateError",
    "ActionCursorError",
    "StructureError",
    "RangeConstructionError",
)


class ActError(Exception):
    ...


class ArgumentError(ActError):
    ...


class FlagError(ActError):
    ...


class ReturningError(ActError):
    ...


class UnionError(ActError):
    ...


class InvalidInitializationError(ActError):
    ...


class AtomizationError(ActError):
    ...


class MatchingError(ActError):
    ...


class ActionChainError(ActError):
    ...


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
