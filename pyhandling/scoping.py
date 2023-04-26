from inspect import stack
from operator import attrgetter
from typing import Any

from pyhandling.synonyms import repeating
from pyhandling.utils import times


__all__ = ("back_scope_in", "value_in")


def back_scope_in(number_of_backs: int, /) -> dict[str, Any]:
    """Function to get scope up the call stack starting from the called scope."""

    scope = repeating(
        attrgetter("f_back"),
        times(number_of_backs + 1),
    )(stack()[1][0])

    return dict() if scope is None else scope.f_locals


def value_in(__name: str, /, *, scope_in: int = 0) -> Any:
    """Function to get value from an external scope."""

    __scope = back_scope_in(scope_in + 1)
    del scope_in

    return __scope[__name] if __name in __scope.keys() else eval(__name)
