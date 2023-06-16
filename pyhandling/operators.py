from typing import Iterable, Callable, Generator, Any
import operator

from pyhandling.annotations import V
from pyhandling.atomization import atomically
from pyhandling.data_flow import by
from pyhandling.partiality import partial
from pyhandling.tools import (
    documenting_by, to_check, LeftCallable, action_repr_of
)


__all__ = (
    "are_linear",
    "inclusive_all",
    "not_inclusive_any",
    "not_",
    "or_",
    "and_",
    "div",
)


class _DynamicDeterminant:
    """
    Class for using synonyms of comparison operators as checking values and
    decorating actions with this synonym.
    """

    def __init__(
        self,
        name: str,
        sum_: Callable[Iterable[Callable[V, Any]], bool],
        *determinats: V | Callable[V, Any]
    ):
        self._name = name
        self._sum = sum_
        self._checkers = tuple(map(to_check, determinats))

        self._sign = self._sum(determinats)

    def __bool__(self) -> bool:
        return self._sign

    def __repr__(self) -> str:
        return "{} ({})".format(
            "positive" if self else "negative",
            (
                f"{self._name} {action_repr_of(self._checkers[0])}"
                if len(self._checkers) == 1
                else f" {self._name} ".join(map(action_repr_of, self._checkers))
            ),
        )

    def __call__(self, value: V) -> bool:
        return self._sum(map(operator.call |by| value, self._checkers))


def are_linear(
    values: Iterable[V],
    checker: Callable[[V, V], bool],
    *,
    sum_: Callable[Generator[bool, None, None], bool] = all,
) -> bool:
    """
    Function for checking a set of values using a binary checker.

    Sequentially checks all values i.e. `(a, b)` then `(b, c)` and so on.
    Combines check results by `sum_` argument.
    """

    values = tuple(values)

    return sum_(
        checker(first, values[index + 1])
        for index, first in enumerate(values[:-1])
    )


def inclusive_all(values: Iterable) -> bool:
    """`all` with `False` when called from an empty collection."""

    return len(tuple(values)) > 0 and all(values)


def not_inclusive_any(values: Iterable) -> bool:
    """`any` with `True` when called from an empty collection."""

    return len(tuple(values)) == 0 or any(values)


not_ = partial(_DynamicDeterminant, 'not', lambda args: operator.not_(*args))

or_ = partial(_DynamicDeterminant, 'or', any)
and_ = partial(_DynamicDeterminant, 'and', all)


div: LeftCallable[[int | float, int | float], float] = documenting_by(
    """Synonym function for `operator.truediv`."""
)(
    atomically(operator.truediv)
)
