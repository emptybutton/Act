from abc import ABC, abstractmethod
from typing import Self, Iterator, Any, Generic

from pyannotating import Special

from pyhandling.annotations import ValueT, FlagT, checker
from pyhandling.errors import FlagError


class Flag(ABC, Generic[ValueT]):
    """Abstract class for atomic objects."""

    @property
    @abstractmethod
    def original(self) -> ValueT:
        ...

    @abstractmethod
    def __sub__(self, other: Self) -> Self:
        ...

    @abstractmethod
    def __mul__(self, other: Self | int) -> Self:
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Self]:
        ...

    @abstractmethod
    def _atomically_equal_to(self, other: Any) -> bool:
        ...

    @abstractmethod
    def _atomically_multiplied_by(self, other: Self | int) -> Self:
        ...

    def __contains__(self, which: Special[checker]) -> bool:
        return (
            any(which(flag.original) for flag in self)
            if callable(which)
            else which in tuple(self)
        )

    def __instancecheck__(self,  instance: Special[Self]) -> bool:
        return self == instance

    def __or__(self, other: Self) -> Self:
        return flag_sum(self, other)

    def __ror__(self, other: Self) -> Self:
        return flag_sum(other, self)

    def __eq__(self, other: Special[Self]) -> bool:
        return (
            other == self
            if isinstance(other, _UnionFlag) and not isinstance(self, _UnionFlag)
            else self._atomically_equal_to(other)
        )

    def __mul__(self, other: Self | int) -> Self:
        return (
            other == self
            if isinstance(other, _UnionFlag) and not isinstance(self, _UnionFlag)
            else self._atomically_multiplied_by(other)
        )
