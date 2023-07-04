from dataclasses import dataclass
from typing import TypeVar, Callable, Generic


__all__ = ("Access", )


_GetterT = TypeVar("_GetterT", bound=Callable)
_SetterT = TypeVar("_SetterT", bound=Callable)


@dataclass(frozen=True)
class Access(Generic[_GetterT, _SetterT]):
    """Aggregate class of getter and setter actions."""

    get: _GetterT
    set: _SetterT
