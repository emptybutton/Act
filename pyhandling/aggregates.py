from dataclasses import dataclass
from typing import TypeVar, Callable, Generic, Optional, Self, Final, Mapping, Any

from pyhandling.annotations import O, P, V, G, S, A, B


__all__ = (
    "Access",
)


_GetterT = TypeVar("_GetterT", bound=Callable)
_SetterT = TypeVar("_SetterT", bound=Callable)


@dataclass(frozen=True)
class Access(Generic[_GetterT, _SetterT]):
    """Aggregate class of getter and setter functions."""

    get: _GetterT
    set: _SetterT
