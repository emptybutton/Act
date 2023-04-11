from abc import ABC, abstractmethod
from functools import reduce
from itertools import chain
from typing import Self, Iterator, Any, Generic, TypeVar, Protocol, Callable, Optional
from operator import or_, sub, attrgetter

from pyannotating import Special

from pyhandling.atoming import atomic
from pyhandling.annotations import ValueT, FlagT, checker_of, PointT, P, ResultT, merger_of, reformer_of
from pyhandling.branching import on
from pyhandling.errors import FlagError
from pyhandling.immutability import to_clone
from pyhandling.language import then, by
from pyhandling.signature_assignmenting import calling_signature_of
from pyhandling.synonyms import returned


__all__ = ("Flag", "flag", "pointed", "nothing")


class Flag(ABC, Generic[PointT]):
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
    nothing | nothing is nothing
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

    bool(flag_to(0) | super_) is True
    bool(flag_to(0) | not_super) is False
    ```

    To select flags by their `point` use the `of` method
    ```
    flag_to(*range(11)).of(lambda n: n >= 7) == flag_to(7, 8, 9, 10)
    flag_to(*range(11)).of(lambda n: n >= 20) == nothing

    super_.of(lambda f: f == super_) == super_
    super_.of(lambda n: n > 0) == nothing
    ```

    Flag sums can be represented in atomic form. In this case, the atomic
    version is technically a representation of all the summed flags in one flag,
    but in fact, it is just a first selected flag.

    Don't use the atomic form to get exactly a first flag. The flag sum does not
    guarantee the preservation of the sequence (although it still implements it).
    ```
    atom = atomic(flag_to(1, 2, 3))

    atom == flag_to(1)
    atom != flag_to(2)
    atom != flag_to(3)

    atomic(flag_to(1)) == flag_to(1)
    ```

    Flags available for instance checking as a synonym for equality.
    ```
    isinstance(instance, instance) is True
    isinstance(first, first | second) is True
    isinstance(first, second) is False
    ```
    """

    _comparison_priority: int | float = 0

    @property
    @abstractmethod
    def point(self) -> PointT:
        ...

    @abstractmethod
    def __getatom__(self) -> Self:
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
    def __mul__(self, times: int) -> Self:
        ...

    @abstractmethod
    def __pos__(self) -> "_FlagVector":
        ...

    @abstractmethod
    def __neg__(self) -> "_FlagVector":
        ...

    @abstractmethod
    def of(self, is_for_selection: checker_of[PointT]) -> Self:
        ...

    def __invert__(self) -> Self:
        return self

    def __instancecheck__(self,  instance: Any) -> bool:
        return self == instance

    def __rmul__(self, times: int) -> Self:
        return self * times

    def __or__(self, other: Special[Self]) -> Self:
        return self.__sum(self, pointed(other), merge=_FlagSum)

    def __ror__(self, other: Special[Self]) -> Self:
        return self.__sum(pointed(other), self, merge=_FlagSum)

    def __eq__(self, other: Special[Self]) -> bool:
        return (
            other == self if (
                isinstance(other, Flag)
                and self._comparison_priority < other._comparison_priority
            )
            else self._atomically_equal_to(other)  
        )

    @abstractmethod
    def _atomically_equal_to(self, other: Any) -> bool:
        ...

    @staticmethod
    def __sum(first: Self, second: Self, *, merge: merger_of[Self]) -> Self:
        if first == nothing:
            return second

        elif second == nothing:
            return first

        elif first == second:
            return first

        else:
            return merge(first, second)


class _FlagVector:
    def __init__(
        self,
        flag: Flag,
        *,
        is_positive: bool = True,
        next_: Optional[reformer_of[Flag]] = None
    ):
        self._flag = flag
        self._is_positive = is_positive
        self._next = next_

    def __repr__(self) -> str:
        return f"{'+' if self._is_positive else '-'}{self._flag}{{}}".format(
            f" ^ {self._next}" if self._next is not None else str()
        )

    @to_clone
    def __xor__(self, other: Self) -> None:
        self._next = other

    @to_clone
    def __neg__(self) -> None:
        self._is_positive = not self._is_positive

    def __pos__(self) -> Self:
        return self

    def __invert__(self) -> Flag:
        return self(nothing)

    def __lshift__(self, flag: Flag) -> Flag:
        return self(flag)

    def __call__(self, flag: Flag) -> Flag:
        action = (or_ if self._is_positive else sub)
        next_ = self._next if self._next is not None else returned

        return flag >= (action |by| self._flag) |then>> next_


_FirstPointT = TypeVar("_FirstPointT")
_SecondPointT = TypeVar("_SecondPointT")


class _DoubleFlag(Flag, ABC):
    _separation_sign: str = ', '
    _comparison_priority = 1

    def __init__(self, first: Flag[_FirstPointT], second: Flag[_SecondPointT]):
        self._first = first
        self._second = second

        if self == nothing:
            raise FlagError("Combining with \"nothing\"")

    @property
    def point(self) -> Self:
        return self

    def __repr__(self) -> str:
        to_repr_of = on(isinstance |by| _ValueFlag, attrgetter("_value"))

        return f"{to_repr_of(self._first)} {self._separation_sign} {to_repr_of(self._second)}"

    def __getatom__(self) -> Flag:
        return atomic(self._first)

    def __mul__(self, times: int) -> Flag:
        return self._combined(self._first * times, self._second * times)

    def __pos__(self) -> _FlagVector:
        return _FlagVector(self._first, next_=_FlagVector(self._second))

    def __neg__(self) -> _FlagVector:
        return _FlagVector(
            self._first,
            is_positive=False,
            next_=_FlagVector(self._second, is_positive=False)
        )

    def __hash__(self) -> int:
        return hash(self._first) + hash(self._second)

    def __sub__(self, other: Any) -> Flag:
        if isinstance(other, _DoubleFlag):
            return self - other._second - other._first

        reduced_second = self._second - other

        if tuple(reduced_second) != tuple(self._second):
            return self._combined(self._first, reduced_second)

        reduced_first = self._first - other

        if tuple(reduced_first) != tuple(self._first):
            return self._combined(reduced_first, self._second)

        return self

    def __len__(self) -> int:
        return len(self._first) + len(self._second)

    def __iter__(self) -> Iterator[Flag]:
        return chain(self._first, self._second)

    def of(self, is_for_selection: checker_of[_FirstPointT | _SecondPointT]) -> Flag:
        return self._combined(
            self._first.of(is_for_selection),
            self._second.of(is_for_selection),
        )

    @abstractmethod
    def _combined(self, first: Flag, second: Flag) -> Flag:
        ...


class _FlagSum(_DoubleFlag):
    """
    Flag sum class.

    Created via the `|` operator between flags or by using tshe `pointed`
    function, which is a safe flag sum constructor.

    Not safe for self-initialization because it has no mechanisms to prevent
    summation with `nothing`.

    Throws `FlagError` when created with `nothing`.

    Recursively delegates calls to its two stored flags.
    Indicates the sum of its flags (self).
    Binary between its flags in `or` form.
    """

    _separation_sign = '|'

    def __bool__(self) -> bool:
        return bool(self._first or self._second)

    def _atomically_equal_to(self, other: Any) -> bool:
        return self._first == other or self._second == other

    def _combined(self, first: Flag, second: Flag) -> Flag:
        return first | second


class _AtomicFlag(Flag, ABC):
    """Class representing flag sum atomic unit."""

    def __getatom__(self) -> Self:
        return self

    def __mul__(self, times: int) -> Flag:
        if times <= 0:
            return nothing
        elif times == 1:
            return self
        else:
            return self | (self * (times - 1))

    def __pos__(self) -> _FlagVector:
        return _FlagVector(self)

    def __neg__(self) -> _FlagVector:
        return _FlagVector(self, is_positive=False)

    def __sub__(self, other: Any) -> Self: 
        return nothing if self == other else self

    def __len__(self) -> int:
        return 1 if self != nothing else 0

    def __iter__(self) -> Iterator[Self]:
        return iter((self, ) if self != nothing else tuple())
 
    def of(self, is_for_selection: checker_of[PointT]) -> Self:
        return self if self != nothing and is_for_selection(self.point) else nothing

    def _atomically_equal_to(self, other: Any) -> bool:
        return type(self) is type(other) and hash(self) == hash(other)


class _ValueFlag(_AtomicFlag, Generic[ValueT]):
    """
    Atomic flag class pointing to some value.

    Not safe for initialization as there is no mechanism to prevent pointing to
    another flag.

    To create, use the `as_flag` method or the `flag_to` function preferably.

    Throws a `FlagError` when created with a flag.

    Delegates `__hash__` and `__bool__` to the pointing value.
    """

    def __init__(self, value: ValueT):
        self._value = value

        if isinstance(self._value, Flag):
            raise FlagError("Flag pointing to another flag")

    @property
    def point(self) -> ValueT:
        return self._value

    def __repr__(self) -> str:
        return f"pointed({self._value})"

    def __hash__(self) -> int:
        return hash(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    @classmethod
    def as_flag(cls, value: FlagT | ValueT) -> FlagT | Flag[ValueT]:
        return value if isinstance(value, Flag) else cls(value)


class _NominalFlag(_AtomicFlag):
    """
    Atomic named flag class.

    Indicates an abstract phenomenon expressed by this flag itself.
    Binary in its sign.

    The public constructor of this class is the `flag` function.
    """

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


class _ActionFlag(_NominalFlag):
    def __init__(self, name: str, sign: bool, action: Callable[P, ResultT]):
        super().__init__(name, sign)

        self._action = action
        self.__signature__ = calling_signature_of(action)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self._action(*args, **kwargs)


def flag(
    name: str,
    *,
    sign: bool = True,
    action: Optional[Callable] = None
) -> _NominalFlag | _ActionFlag:
    """
    Function constructor of an atomic named flag pointing to itself.
    See `Flag` for behavior info.
    """

    return _NominalFlag(name, sign) if action is None else _ActionFlag(name, sign, action)


def pointed(*values: FlagT | ValueT) -> FlagT | _ValueFlag[ValueT]:
    """
    Function to create a flag sum pointing to input values.
    See `Flag` for behavior info.
    """

    flags = tuple(map(_ValueFlag.as_flag, values))

    if len(flags) == 0:
        return nothing
    elif len(flags) == 1:
        return flags[0]

    return reduce(or_, flags)


nothing = flag("nothing", sign=False)
nothing.__doc__ = (
    """
    Special flag identifying the absence of a flag.
    Is a neutral element in flag sum operations.
    """
)