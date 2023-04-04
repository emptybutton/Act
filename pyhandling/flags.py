from abc import ABC, abstractmethod
from itertools import chain
from typing import Self, Iterator, Any, Generic

from pyannotating import Special

from pyhandling.annotations import ValueT, FlagT, checker
from pyhandling.errors import FlagError


__all__ = ("Flag", "ValueFlag", "flag", "flag_sum", "as_flag", "nothing")


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
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Self]:
        ...

    @abstractmethod
    def _atomically_equal_to(self, other: Any) -> bool:
        ...

    @abstractmethod
    def _atomically_multiplied_by(self, value: int) -> Self:
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

    def __mul__(self, other: int) -> Self:
        return (
            other * self
            if isinstance(other, _UnionFlag) and not isinstance(self, _UnionFlag)
            else self._atomically_multiplied_by(other)
        )


class _UnionFlag(Flag):
    def __init__(self, first: Flag, second: Flag):
        self._first = first
        self._second = second

        if self == nothing:
            raise FlagError("Combining with \"nothing\"")

    @property
    def original(self) -> Self:
        return self

    def __repr__(self) -> str:
        return f"{self.__format_flag(self._first)} | {self.__format_flag(self._second)}"

    def __hash__(self) -> int:
        return hash(self._first) + hash(self._second)

    def __bool__(self) -> bool:
        return bool(self._first or self._second)

    def __sub__(self, other: Flag) -> Flag:
        if isinstance(other, _UnionFlag):
            return self - other._second - other._first

        reduced_second = self._second - other

        if reduced_second != self._second:
            return self._first | reduced_second

        reduced_first = self._first - other

        if reduced_first != self._first:
            return reduced_first | self._second

        return self

    def __len__(self) -> int:
        return len(self._first) + len(self._second)

    def __iter__(self) -> Iterator[Flag]:
        return chain(self._first, self._second)

    def has_type(self, type_: type) -> bool:
        return self

    def _atomically_equal_to(self, other: Any) -> bool:
        return self._first == other or self._second == other

    def _atomically_multiplied_by(self, value: int) -> Self:
        return (self._first * value) | (self._second * value)

    @staticmethod
    def __format_flag(flag: Flag) -> str:
        return str(flag.value if isinstance(flag, ValueFlag) else flag)


class _AtomicFlag(Flag, ABC):
    def __sub__(self, other: Any) -> Self: 
        return nothing if self == other else self

    def __len__(self) -> int:
        return 1

    def __iter__(self) -> Iterator[Self]:
        return iter((self, ))

    def _atomically_equal_to(self, other: Any) -> bool:
        return type(self) is type(other) and hash(self) == hash(other)

    def _atomically_multiplied_by(self, value: int) -> Self:
        if value <= 0:
            return nothing
        elif value == 1:
            return self
        else:
            return self | (self * (value - 1))


class ValueFlag(_AtomicFlag, Generic[ValueT]):
    def __init__(self, value: ValueT, *, identifiable_by_type: bool = False):
        self._value = value
        self._is_identifiable_by_type = identifiable_by_type

    @property
    def original(self) -> ValueT:
        return self._value

    @property
    def is_identifiable_by_type(self) -> bool:
        return self._is_identifiable_by_type

    def __repr__(self) -> str:
        return f"flag({self._value})"

    def __hash__(self) -> int:
        return hash(
            type(self._value) if self._is_identifiable_by_type else self._value
        )


class _NominalFlag(_AtomicFlag):
    def __init__(self, name: str, sign: bool):
        self._name = name
        self._sign = sign

    @property
    def original(self) -> Self:
        return self

    def __repr__(self) -> str:
        return self._name

    def __hash__(self) -> int:
        return hash(self._name + str(int(self._sign)))

    def __bool__(self) -> bool:
        return self._sign


def flag(name: str, *, sign: bool = True) -> Flag:
    return _NominalFlag(name, sign)


def flag_sum(first: Flag, second: Flag) -> Flag:
    if first == nothing:
        return second

    elif second == nothing:
        return first

    else:
        return _UnionFlag(first, second)


def as_flag(value: FlagT | ValueT) -> FlagT | ValueFlag[ValueT]:
    return value if isinstance(value, Flag) else ValueFlag(value)


nothing = flag("nothing", sign=False)
nothing.__doc__ = """Flag to indicate the absence of anything, including `None`."""
