from abc import ABC, abstractmethod
from functools import reduce
from itertools import chain
from typing import Self, Iterator, Any, Generic
from operator import or_

from pyannotating import Special

from pyhandling.annotations import ValueT, FlagT, checker
from pyhandling.errors import FlagError


__all__ = ("Flag", "flag", "flag_to", "flag_sum", "nothing")


class Flag(ABC, Generic[ValueT]):
    """
    Base class of atomic unique values and their algebraic operations.
    
    Add instances with `|` operator and subtract with `-`.
    Checks for the presence of an instance using the `==` operator.

    Adds by `or` nature so
    ```
    first | second == first
    first | second == second
    first | second == first | second
    first | second == first | third
    ```

    Subtracts optional so
    ```
    first - second == first
    (first | second) - second == first
    ```

    Has a specific `nothing` instance that is a neutral element so
    ```
    instance | nothing == instance
    instance | nothing != nothing

    instance - instance == nothing

    nothing == nothing
    nothing | nothing == nothing
    ```

    To create a sum of flags without the `|` operator, there is the `flag_sum`
    function.
    ```
    flag_sum(first, second, third) == first | second | third
    flag_sum(instance, nothing) == instance
    flag_sum(instance) == instance
    flag_sum() == nothing
    ```

    According to this addition logic, there is a multiplication
    ```
    instance * 2 == instance | instance
    instance * 1 == instance
    instance * 0 == nothing
    instance * -1 == nothing
    (first | second) * 2 == first | first | second | second
    ```

    Iterable by its sum so
    ```
    tuple(first | second | third) == (first, second, third)
    len(first | second | third) == 3

    tuple(instance) == (instance, )
    len(instance) == 1

    tuple(nothing) == tuple()
    len(nothing) = 0
    ```

    Flags indicate something. It can be any value or abstract phenomenon
    expressed only by this flag.

    Flags indicating a value can be obtained via the `flag_to` function. Flags
    for abstract phenomena (or named flags) via the `flag` function.
    ```
    super_ = flag("super")

    super_.point == super_
    flag_to(1).point == 1

    nothing.point == nothing

    (first | second).point == first | second
    ```

    The `flag_to` function is also a sum function.
    ```
    flag_to(1, 2, 3) == flag_to(1) | flag_to(2) | flag_to(3)
    ```

    Flags indicating a value are binary by value. Nominal by their signs.
    ```
    not_super = flag("not_super", sign=False)

    bool(super_) is True
    bool(not_super) is False

    bool(flag_to(1)) is True
    bool(flag_to(0)) is False

    bool(flag_to[0] | super_) is True
    bool(flag_to[0] | not_super) is False
    ```
    """

    @property
    @abstractmethod
    def point(self) -> ValueT:
        ...

    @property
    @abstractmethod
    def atomic(self) -> Self:
        ...

    @abstractmethod
    def __sub__(self, other: Any) -> Self:
        ...

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Self]:
        ...

    @abstractmethod
    def __getitem__(self, which: checker) -> Self:
        ...

    @abstractmethod
    def _atomically_equal_to(self, other: Any) -> bool:
        ...

    @abstractmethod
    def _atomically_multiplied_by(self, times: int) -> Self:
        ...

    def __instancecheck__(self,  instance: Any) -> bool:
        return self == instance

    def __or__(self, other: Self) -> Self:
        return self._combine_flags(self, other)

    def __ror__(self, other: Self) -> Self:
        return self._combine_flags(other, self)

    def __eq__(self, other: Special["_UnionFlag"]) -> bool:
        return (
            other == self
            if isinstance(other, _UnionFlag) and not isinstance(self, _UnionFlag)
            else self._atomically_equal_to(other)
        )

    def __mul__(self, times: int) -> Self:
        return (
            times * self
            if isinstance(times, _UnionFlag) and not isinstance(self, _UnionFlag)
            else self._atomically_multiplied_by(times)
        )

    def __rmul__(self, other: int) -> Self:
        return self * other

    @staticmethod
    def _combine_flags(first: Self, second: Self) -> Self:
        if first == nothing:
            return second

        elif second == nothing:
            return first

        else:
            return _UnionFlag(first, second)


class _UnionFlag(Flag):
    def __init__(self, first: Flag, second: Flag):
        self._first = first
        self._second = second

        if self == nothing:
            raise FlagError("Combining with \"nothing\"")

    @property
    def point(self) -> Self:
        return self

    @property
    def atomic(self) -> Flag:
        return self._first.atomic

    def __repr__(self) -> str:
        return f"{self._first} | {self._second}"

    def __hash__(self) -> int:
        return hash(self._first) + hash(self._second)

    def __bool__(self) -> bool:
        return bool(self._first or self._second)

    def __sub__(self, other: Any) -> Flag:
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

    def __getitem__(self, which: checker) -> Flag:
        return self._combine_flags(self._first[which], self._second[which])

    def _atomically_equal_to(self, other: Any) -> bool:
        return self._first == other or self._second == other

    def _atomically_multiplied_by(self, times: int) -> Self:
        return (self._first * times) | (self._second * times)


class _AtomicFlag(Flag, ABC):
    @property
    def atomic(self) -> Self:
        return self

    def __sub__(self, other: Any) -> Self: 
        return nothing if self == other else self

    def __len__(self) -> int:
        return 1 if self != nothing else 0

    def __iter__(self) -> Iterator[Self]:
        return iter((self, ) if self != nothing else tuple())
 
    def __getitem__(self, which: checker) -> Self:
        return self if self != nothing and which(self.point) else nothing

    def _atomically_equal_to(self, other: Any) -> bool:
        return type(self) is type(other) and hash(self) == hash(other)

    def _atomically_multiplied_by(self, times: int) -> Self:
        if times <= 0:
            return nothing
        elif times == 1:
            return self
        else:
            return self | (self * (times - 1))


class _ValueFlag(_AtomicFlag, Generic[ValueT]):
    def __init__(self, value: ValueT):
        self._value = value

        if isinstance(self._value, Flag):
            raise FlagError("Flag pointing to another flag")

    @property
    def point(self) -> ValueT:
        return self._value

    def __repr__(self) -> str:
        return f"flag[{self._value}]"

    def __hash__(self) -> int:
        return hash(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    @classmethod
    def as_flag(cls, value: FlagT | ValueT) -> FlagT | Flag[ValueT]:
        return value if isinstance(value, Flag) else cls(value)


class _NominalFlag(_AtomicFlag):
    def __init__(self, name: str, sign: bool):
        self._name = name
        self._sign = sign

    @property
    def point(self) -> Self:
        return self

    def __repr__(self) -> str:
        return self._name

    def __hash__(self) -> int:
        return hash(self._name + str(int(self._sign)))

    def __bool__(self) -> bool:
        return self._sign


def flag(name: str, *, sign: bool = True) -> Flag:
    return _NominalFlag(name, sign)


def flag_to(*values: FlagT | ValueT) -> FlagT | _ValueFlag[ValueT]:
    return flag_sum(*map(_ValueFlag.as_flag, values))


def flag_sum(*flags: Flag) -> Flag:
    if len(flags) == 0:
        return nothing
    elif len(flags) == 1:
        return flags[0]
    else:
        return reduce(or_, flags)


nothing = flag("nothing", sign=False)
nothing.__doc__ = """Flag to indicate the absence of anything, including `None`."""
