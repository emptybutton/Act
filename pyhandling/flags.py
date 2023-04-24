from abc import ABC, abstractmethod
from functools import reduce
from itertools import chain
from typing import (
    Self, Iterator, Any, Generic, TypeVar, Callable, Optional, Tuple,
    Literal, Mapping
)
from operator import or_, sub, attrgetter, not_

from pyannotating import Special

from pyhandling.atoming import atomic
from pyhandling.annotations import (
    ValueT, FlagT, checker_of, PointT, Pm, ResultT, merger_of, reformer_of, A, B
)
from pyhandling.data_flow import by, then
from pyhandling.errors import FlagError
from pyhandling.immutability import to_clone
from pyhandling.partials import fragmentarily
from pyhandling.signature_assignmenting import call_signature_of
from pyhandling.structure_management import (
    with_opened_items, in_collection, dict_of
)
from pyhandling.synonyms import returned, on
from pyhandling.tools import with_attributes


__all__ = (
    "Flag",
    "FlagVector",
    "flag",
    "pointed",
    "to_points",
    "to_value_points",
    "flag_enum_of",
    "pointed_or",
    "nothing",
)


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
    first | second is not first
    ```

    Subtracts optional so
    ```
    first - second is first
    (first | second) - second is first
    ```

    Has a specific `nothing` instance that is a neutral element so
    ```
    instance | nothing is instance
    instance | nothing != nothing

    instance - instance is nothing

    nothing == nothing
    nothing | nothing is nothing
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

    Flags indicating a value can be obtained via the `pointed` function. Flags
    for abstract phenomena (or named flags) via the `flag` function.
    ```
    pointed(4) == 4
    pointed(4) is not 4
    pointed(4) | instance == pointed(4)

    pointed(1, 2, 3) == pointed(1) | pointed(2) | pointed(3)
    pointed(instance) is instance
    pointed() is nothing

    pointed(4).point == 4
    pointed(4).points == (4, )

    super_ = flag("super")
    super_.point is super_
    super_.points == (super_, )

    nothing.point is nothing
    nothing.points == (nothing, )

    (first | second).point == first.point
    (first | second).points == (first.point, second.point)
    ```

    Flags indicating a value are binary by value. Nominal by their signs.
    ```
    not_super = flag("not_super", sign=False)

    bool(super_) is True
    bool(not_super) is False

    bool(pointed(1)) is True
    bool(pointed(0)) is False

    bool(pointed(0) | super_) is True
    bool(pointed(0) | not_super) is False
    ```

    To select flags by their `point` use the `that` method
    ```
    pointed(*range(11)).that(lambda n: n >= 7) == pointed(7, 8, 9, 10)
    pointed(*range(11)).that(lambda n: n >= 20) == nothing

    super_.that(lambda f: f == super_) == super_
    super_.that(lambda n: n > 0) == nothing
    ```

    Flag sums can be represented in atomic form. In this case, the atomic
    version is technically a representation of all flags of the sum, and at the
    same time none, in one flag, but in fact, it is just a first selected flag.

    Don't use the atomic form to get exactly a first flag. The flag sum does not
    guarantee the preservation of the sequence (although it still implements it).
    ```
    atomic(pointed(1, 2, 3)) # pointed(1)
    ```

    Flags can be represented in vector form via unary plus or minus and added
    via `<<` (or via call).
    ```
    pointed(1) != +pointed(1)
    pointed(1) != -pointed(1)

    pointed(1, 2) << +pointed(3) # pointed(1, 2, 3)
    pointed(1, 2, 3) << -pointed(3) # pointed(1, 2)
    (-pointed(1))(pointed(1)) # nothing
    ```

    They also have unary plus and minus and a sum, which can be created with the
    `^` operator and inverted back to flag by `~` operator.
    ```
    ++pointed(1) # +pointed(1)
    --pointed(1) # +pointed(1)

    ~+pointed(1) == pointed(1)
    ~-pointed(1) is nothing

    pointed(1) << +pointed(2) # pointed(1, 2)

    pointed(1, 2) << (-pointed(2) ^ +pointed(3)) # pointed(1, 3)
    ```

    Flags also use `~` to come to themselves, which can be used with a `Union`
    type with a vector to cast to Flag.
    ```
    from random import choice


    ~pointed(1) == pointed(1)

    flag_or_vector = choice([pointed(1), +pointed(1)])

    isinstance(~flag_or_vector, Flag) is True # Always
    isinstance(+flag_or_vector, FlagVector) is True # Always
    ```

    Flags available for instance checking as a synonym for equality.
    ```
    isinstance(4, instance) is False
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

    @property
    @abstractmethod
    def points(self) -> Tuple[PointT]:
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
    def __pos__(self) -> "FlagVector":
        ...

    @abstractmethod
    def __neg__(self) -> "FlagVector":
        ...

    @abstractmethod
    def that(self, is_for_selection: checker_of[PointT]) -> Self:
        ...

    def __invert__(self) -> Self:
        return self

    def __instancecheck__(self,  instance: Any) -> bool:
        return self == instance

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


class FlagVector(ABC):
    """
    Abstract memorization class `Flag` expressions.
    For usage description see `Flag`.
    """

    @abstractmethod
    def __xor__(self, other: Self) -> Self:
        ...

    @abstractmethod
    def __neg__(self) -> Self:
        ...

    @abstractmethod
    def __call__(self, flag: Flag) -> Flag:
        ...

    def __pos__(self) -> Self:
        return self

    def __invert__(self) -> Flag:
        return self(nothing)

    def __lshift__(self, flag: Flag) -> Flag:
        return self(flag)


class _BinaryFlagVector(FlagVector):
    """
    `FlagVector` class that implements the memorization of `Flag` expressions
    and the connection of several `FlagVector`.
    """

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

    def __call__(self, flag: Flag) -> Flag:
        action = (or_ if self._is_positive else sub)
        next_ = self._next if self._next is not None else returned

        return next_(action(flag, self._flag))


_FirstPointT = TypeVar("_FirstPointT")
_SecondPointT = TypeVar("_SecondPointT")


class _DoubleFlag(Flag, ABC):
    """Abstract `Flag` class to combine them."""

    _separation_sign: str = ', '
    _comparison_priority = 1

    def __init__(self, first: Flag[_FirstPointT], second: Flag[_SecondPointT]):
        self._first = first
        self._second = second

        if self == nothing:
            raise FlagError("Combining with \"nothing\"")

    @property
    def point(self) -> Tuple:
        return self._first.point

    @property
    def points(self) -> Tuple:
        return with_opened_items(
            (
                flag.point
                if isinstance(flag.point, _DoubleFlag)
                else in_collection(flag.point)
            )
            for flag in self
        )

    def __repr__(self) -> str:
        to_repr_of = on(isinstance |by| _ValueFlag, attrgetter("_value"))

        return f"{{}} {self._separation_sign} {{}}".format(
            to_repr_of(self._first),
            to_repr_of(self._second),
        )

    def __getatom__(self) -> Flag:
        return atomic(self._first)

    def __pos__(self) -> FlagVector:
        return _BinaryFlagVector(
            self._first,
            next_=_BinaryFlagVector(self._second),
        )

    def __neg__(self) -> FlagVector:
        return _BinaryFlagVector(
            self._first,
            is_positive=False,
            next_=_BinaryFlagVector(self._second, is_positive=False)
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

    def that(
        self,
        is_for_selection: checker_of[_FirstPointT | _SecondPointT],
    ) -> Flag:
        return self._combined(
            self._first.that(is_for_selection),
            self._second.that(is_for_selection),
        )

    @abstractmethod
    def _combined(self, first: Flag, second: Flag) -> Flag:
        ...


class _FlagSum(_DoubleFlag):
    """`DoubleFlag` class for combining flags according to `or` logic."""

    _separation_sign = '|'

    def __bool__(self) -> bool:
        return bool(self._first or self._second)

    def _atomically_equal_to(self, other: Any) -> bool:
        return self._first == other or self._second == other

    def _combined(self, first: Flag, second: Flag) -> Flag:
        return first | second


class _AtomicFlag(Flag, ABC):
    """Class representing flag sum atomic unit."""

    @property
    def points(self) -> Tuple:
        return (self.point, )

    def __getatom__(self) -> Self:
        return self

    def __pos__(self) -> FlagVector:
        return _BinaryFlagVector(self)

    def __neg__(self) -> FlagVector:
        return _BinaryFlagVector(self, is_positive=False)

    def __sub__(self, other: Any) -> Self:
        return nothing if self == other else self

    def __len__(self) -> Literal[0] | Literal[1]:
        return 1 if self != nothing else 0

    def __iter__(self) -> Iterator[Self]:
        return iter((self, ) if self != nothing else tuple())

    def that(self, is_for_selection: checker_of[PointT]) -> Self:
        return (
            self
            if self != nothing and is_for_selection(self.point)
            else nothing
        )

    def _atomically_equal_to(self, other: Any) -> bool:
        return type(self) is type(other) and hash(self) == hash(other)


class _ValueFlag(_AtomicFlag, Generic[ValueT]):
    """
    Atomic flag class pointing to some value.

    Not safe for initialization as there is no mechanism to prevent pointing to
    another flag.

    To create, use the `as_flag` method or the `pointed` function preferably.

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
    """
    `_NominalFlag` class for also implementing delegation call to input action.
    """

    def __init__(self, name: str, sign: bool, action: Callable[Pm, ResultT]):
        super().__init__(name, sign)

        self._action = action
        self.__signature__ = call_signature_of(action)

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> ResultT:
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

    Specifies a flag casting to `bool` given the `sign` parameter.
    When `action` is specified, the resulting flag will be called on that action.
    """

    return (
        _NominalFlag(name, sign)
        if action is None
        else _ActionFlag(name, sign, action)
    )


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


@fragmentarily
def to_points(action: Callable[[A], B], value: A | Flag[A]) -> Flag[B]:
    """Decorator to execute inside `Flag.points`."""

    return pointed(*map(action, pointed(value).points))


@fragmentarily
def to_value_points(action: Callable[[A], B], value: A | Flag[A]) -> Flag[B]:
    """
    Flag `point` execution context of flags whose `points` do not point to
    themselves.
    """

    return to_points(on((isinstance |by| Flag) |then>> not_, action), value)


def flag_enum_of(value: Special[Mapping]) -> object:
    """
    Decorator for creating an `Enum`-like object consisting of `Flags`.

    Creates from an input dictionary if an input value is a dictionary,
    otherwise from attributes of an input object.

    Takes from input values the values that are `Flags`, under their keyword.

    With a value of `...` (`Ellipsis`) generates a flag named keyword, from
    which this value is taken and also takes it.

    Stores all flags taken or generated as a sum in the reserved `flags`
    attribute.
    """

    flag_by_name = {
        name: flag(name) if value is Ellipsis else value
        for name, value in dict_of(value).items()
        if value is Ellipsis or isinstance(value, Flag)
    }

    return with_attributes(**flag_by_name, flags=pointed(*flag_by_name.values()))


pointed_or = AnnotationTemplate(Union, [
    AnnotationTemplate(Flag, [input_annotation]),
    input_annotation,
])


nothing = flag("nothing", sign=False)
nothing.__doc__ = (
    """
    Special flag identifying the absence of a flag.
    Is a neutral element in flag sum operations.

    See `Flag` for behavior info.
    """
)
