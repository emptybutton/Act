from abc import ABC, abstractmethod
from functools import reduce
from itertools import chain
from typing import (
    Self, Iterator, Any, Generic, TypeVar, Callable, Optional, Tuple, Literal,
    ParamSpec
)
from operator import or_, sub, attrgetter, not_

from pyannotating import Special

from act.atomization import atomic
from act.annotations import (
    V, FlagT, checker_of, merger_of, reformer_of, A, B, P, Pm, R, CommentAnnotation
)
from act.data_flow import by, then
from act.errors import FlagError
from act.immutability import to_clone
from act.partiality import partially
from act.representations import code_like_repr_of
from act.synonyms import returned, on
from act.tools import documenting_by


__all__ = (
    "Flag",
    "FlagVector",
    "flag_about",
    "pointed",
    "to_points",
    "to_value_points",
    "nothing",
)


class Flag(ABC, Generic[P]):
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
    len(nothing) == 0
    ```

    Flags indicate something. It can be any value or abstract phenomenon
    expressed only by this flag.

    Flags indicating a value can be obtained via the `pointed` function. Flags
    for abstract phenomena (or named flags) via the `flag_about` function.
    ```
    pointed(4) | instance == pointed(4)

    pointed(1, 2, 3) == pointed(1) | pointed(2) | pointed(3)
    pointed(instance) is instance
    pointed() is nothing

    pointed(4).point == 4
    pointed(4).points == (4, )

    super_ = flag_about("super")
    super_.point is super_
    super_.points == (super_, )

    nothing.point is nothing
    nothing.points == tuple()

    (first | second).point == first.point
    (first | second).points == (first.point, second.point)
    ```

    Flags indicating a value are binary by value. Nominal by their signs.
    ```
    not_super = flag_about("not_super", negative=True)

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
    super_.that(lambda f: f == 0) == nothing
    ```

    Flag sums can be represented in atomic form. In this case, the atomic
    version is technically a representation of all flags of the sum, and at the
    same time none, in one flag, but in fact, it is just a first selected flag.

    Don't use the atomic form to get exactly a first flag. The flag sum does not
    guarantee the preservation of the sequence (although it still implements it).
    ```
    atomic(pointed(1, 2, 3))  # pointed(1)
    ```

    Flags can be represented in vector form via unary plus or minus and added
    via call.
    ```
    pointed(1) != +pointed(1)
    pointed(1) != -pointed(1)

    (+pointed(3))(pointed(1, 2))  # pointed(1, 2, 3)
    (-pointed(3))(pointed(1, 2, 3))  # pointed(1, 2)
    (-pointed(1))(pointed(1))  # nothing
    ```

    They also have unary plus and minus and a sum, which can be created with the
    `^` operator and inverted back to flag by `~` operator.
    ```
    ++pointed(1)  # +pointed(1)
    --pointed(1)  # +pointed(1)

    ~+pointed(1) == pointed(1)
    ~-pointed(1) is nothing

    (+pointed(2))(pointed(1))  # pointed(1, 2)

    (-pointed(2) ^ +pointed(3))(pointed(1, 2))  # pointed(1, 3)
    ```

    Flags also use `~` to come to themselves, which can be used with a `Union`
    type with a vector to cast to Flag.
    ```
    from random import choice


    ~pointed(1) == pointed(1)

    flag_or_vector = choice([pointed(1), +pointed(1)])

    isinstance(~flag_or_vector, Flag) is True  # always
    isinstance(+flag_or_vector, FlagVector) is True  # always
    ```

    Flags available for instance checking as a synonym for `instance` checking
    by `points`.
    ```
    isinstance(4, super_) is False
    isinstance(super_, super_) is True
    isinstance(super_, super_ | not_super) is True
    isinstance(super_, not_super) is False

    isinstance(1, pointed(int)) is True
    isinstance(1, super_ | int) is True
    isinstance(super_, super_ | int) is True
    ```
    """

    _comparison_priority: int | float = 0

    @property
    @abstractmethod
    def point(self) -> P:
        ...

    @property
    @abstractmethod
    def points(self) -> Tuple[P]:
        ...

    @abstractmethod
    def __getatom__(self) -> Self:
        ...

    @abstractmethod
    def __instancecheck__(self, instance: Any) -> bool:
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
    def that(self, is_for_selection: checker_of[P]) -> Self:
        ...

    def __invert__(self) -> Self:
        return self

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
    def __call__(self, value: Special[Flag]) -> Flag:
        ...

    def __pos__(self) -> Self:
        return self

    def __invert__(self) -> Flag:
        return self(nothing)


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
        self.__next = next_

    def __repr__(self) -> str:
        return f"{'+' if self._is_positive else '-'}{self._flag}{{}}".format(
            f" ^ {self._next}" if self.__next is not None else str()
        )

    def __eq__(self, other: Special[Self]) -> bool:
        return (
            isinstance(other, _BinaryFlagVector)
            and self._is_positive is other._is_positive
            and self._flag.points == other._flag.points
        )

    @to_clone
    def __xor__(self, other: Self) -> None:
        self.__next = other

    @to_clone
    def __neg__(self) -> None:
        self._is_positive = not self._is_positive

    def __call__(self, value: Special[Flag]) -> Flag:
        return self._next(self._action(pointed(value), self._flag))

    @property
    def _next(self) -> Callable[Special[Flag], Flag]:
        return self.__next if self.__next is not None else returned

    @property
    def _action(self) -> Callable[Flag, Flag]:
        return or_ if self._is_positive else sub


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
        points = list()

        for flag in self:
            points.extend(
                flag.point
                if isinstance(flag.point, _DoubleFlag)
                else (flag.point, )
            )

        return tuple(points)

    def __repr__(self) -> str:
        value_of = on(isinstance |by| _ValueFlag, attrgetter("_value"))

        return f"{{}} {self._separation_sign} {{}}".format(
            code_like_repr_of(value_of(self._first)),
            code_like_repr_of(value_of(self._second)),
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

    def __instancecheck__(self, instance: Any) -> bool:
        return (
            isinstance(instance, self._first)
            or isinstance(instance, self._second)
        )

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
        return tuple() if self is nothing else (self.point, )

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

    def that(self, is_for_selection: checker_of[P]) -> Self:
        return (
            self
            if self != nothing and is_for_selection(self.point)
            else nothing
        )


class _ValueFlag(_AtomicFlag, Generic[V]):
    """
    Atomic flag class pointing to some value.

    Not safe for initialization as there is no mechanism to prevent pointing to
    another flag.

    To create, use the `as_flag` method or the `pointed` function preferably.

    Throws a `FlagError` when created with a flag.

    Delegates `__hash__` and `__bool__` to the pointing value.
    """

    def __init__(self, value: V):
        self._value = value

        if isinstance(self._value, Flag):
            raise FlagError("Flag pointing to another flag")

    @property
    def point(self) -> V:
        return self._value

    def __repr__(self) -> str:
        return f"pointed({code_like_repr_of(self._value)})"

    def __hash__(self) -> int:
        return hash(self._value) + 10*19

    def __bool__(self) -> bool:
        return bool(self._value)

    def __instancecheck__(self, instance: Any) -> bool:
        return isinstance(instance, self.point)

    @classmethod
    def as_flag(cls, value: FlagT | V) -> FlagT | Flag[V]:
        return value if isinstance(value, Flag) else cls(value)

    def _atomically_equal_to(self, other: Special[Self]) -> bool:
        return type(self) is type(other) and self._value == other._value


class _BaseNamedFlag(_AtomicFlag):
    """Self-pointing atomic flag class."""

    def __init__(self, name: str, /, *, negative: bool = False):
        self._name = name
        self._sign = not negative

    @property
    def point(self) -> Self:
        return self

    def __repr__(self) -> str:
        return self._name

    def __hash__(self) -> int:
        return hash(self._name) + hash(self._sign)

    def __bool__(self) -> bool:
        return self._sign

    def __instancecheck__(self, instance: Any) -> bool:
        return self == instance

    def _atomically_equal_to(self, other: Special[Self]) -> bool:
        return (
            type(self) is type(other)
            and self._name == other._name
            and self._sign is other._sign
        )


_FirstPm = ParamSpec("_FirstPm")


class _CallableNamedFlag(_BaseNamedFlag, Generic[Pm, R]):
    def __init__(
        self,
        name: str,
        /,
        *,
        negative: bool = False,
        action: Callable[Pm, R],
    ):
        super().__init__(name, negative=negative)
        self._action = action
        self._annotation = CommentAnnotation(self._name)

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._action(*args, **kwargs)

    def __getitem__(self, annotation: Special[tuple]) -> CommentAnnotation:
        return self._annotation[annotation]

    def to(
        self,
        action: Callable[_FirstPm, Pm],
    ) -> "_CallableNamedFlag[_FirstPm, R]":
        return _CallableNamedFlag(
            self._name,
            negative=not self._sign,
            action=action |then>> self._action
        )


class _NamedFlag(_BaseNamedFlag):
    """
    _BaseNamedFlag class that can become callable when calling the `to` method
    with an action.
    """

    def to(self, action: Callable[Pm, R]) -> _CallableNamedFlag[Pm, R]:
        """Method to get an callable version of a flag by an input action."""

        return _CallableNamedFlag(
            self._name,
            negative=not self._sign,
            action=action,
        )


def flag_about(name: str, /, *, negative: bool = False) -> _NamedFlag:
    """
    Constructor of an atomic named flag pointing to itself.
    See `Flag` for behavior info.

    When `negative` is `True`, casts to `False` when cast to `bool`.
    """

    return _NamedFlag(name, negative=negative)


def pointed(*values: FlagT | V) -> FlagT | _ValueFlag[V]:
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


@partially
def to_points(action: Callable[[A], B], value: A | Flag[A]) -> Flag[B]:
    """Decorator to execute inside `Flag.points`."""

    return pointed(*map(action, pointed(value).points))


@partially
def to_value_points(action: Callable[[A], B], value: A | Flag[A]) -> Flag[B]:
    """
    Flag `point` execution context of flags whose `points` do not point to
    themselves.
    """

    return to_points(on((isinstance |by| Flag) |then>> not_, action), value)


nothing = documenting_by(
    """
    Special flag identifying the absence of a flag.
    Is a neutral element in flag sum operations.

    See `Flag` for behavior info.
    """
)(
    flag_about("nothing", negative=True)
)
