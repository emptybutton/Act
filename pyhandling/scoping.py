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

