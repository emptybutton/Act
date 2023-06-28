from typing import Callable, Optional, Type, NoReturn

from act.annotations import Pm, R, ErrorT
from act.atomization import atomically
from act.contexting import contextual
from act.data_flow import by, to, eventually
from act.partiality import partially
from act.pipeline import binding_by, then
from act.synonyms import trying_to, raise_
from act.tools import documenting_by, LeftCallable


__all__ = (
    "with_error",
    "catching",
    "raising",
)


with_error: LeftCallable[
    [Callable[Pm, R]],
    LeftCallable[Pm, contextual[Optional[R], Optional[Exception]]]
]
with_error = documenting_by(
    """
    Decorator that causes the decorated function to return the error that
    occurred.

    Returns in `contextual` format (result, error).
    """
)(
    atomically(
        binding_by(... |then>> contextual)
        |then>> (trying_to |by| to(contextual |to| None))
    )
)


@partially
def catching(
    error_type_to_catch: Type[ErrorT],
    action: Callable[ErrorT, R],
    error: ErrorT,
) -> R:
    """
    Function to optionally handle an input error depending on its type.

    Throws an input error if an input error type does not match the expected
    type.
    """

    if not isinstance(error, error_type_to_catch):
        raise error

    return action(error)


raising: LeftCallable[Exception, LeftCallable[..., NoReturn]]
raising = documenting_by(
    """
    Constructor of an action that raises an input error ignoring input
    arguments.
    """
)(
    eventually |to| raise_
)