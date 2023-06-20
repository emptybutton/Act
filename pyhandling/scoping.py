from inspect import stack
from operator import attrgetter
from typing import Any

from pyhandling.iteration import times
from pyhandling.synonyms import repeating


__all__ = ("back_scope_in", "value_in")


def back_scope_in(number_of_backs: int, /):
    """Function to get scope up the call stack starting from the called scope."""

    scope = repeating(
        attrgetter("f_back"),
        times(number_of_backs),
    )(stack()[1][0])

    return scope


def value_in(name: str, /, *, scope_in: int = 0) -> Any:
    """Function to get value from an external scope."""

    scope = back_scope_in(scope_in + 1)

    if scope is not None:
        if name in scope.f_locals.keys():
            return scope.f_locals[name]

    return eval(name)
