from functools import partial
from operator import not_, add
from typing import Callable, Optional

from pyhandling.annotations import dirty, handler_of, ValueT, ResultT, checker_of, action_for, P, reformer_of
from pyhandling.atoming import atomically
from pyhandling.branchers import on, rollbackable, binding_by
from pyhandling.contexting import contextual
from pyhandling.data_flow import returnly, eventually
from pyhandling.flags import nothing
from pyhandling.language import then, by, to
from pyhandling.partials import closed, right_partial
from pyhandling.tools import documenting_by, Clock


__all__ = (
    "shown",
    "isnt",
    "times",
    "with_error",
)


shown: dirty[reformer_of[ValueT]]
shown = documenting_by("""Shortcut function for `returnly(print)`.""")(
    returnly(print)
)


isnt: Callable[[handler_of[ValueT]], checker_of[ValueT]]
isnt = documenting_by("""Negation adding function.""")(
    binding_by(... |then>> not_)
)


times: Callable[[int], dirty[action_for[bool]]] = documenting_by(
    """
    Function to create a function that will return `True` the input value (for
    this function) number of times, then `False` once after the input count has
    passed, `True` again n times, and so on.

    Resulting function is independent of its input arguments.
    """
)(
    atomically(
        (add |by| 1)
        |then>> Clock
        |then>> closed(
            on(
                not_,
                returnly(lambda clock: (setattr |to| clock)(
                    "ticks_to_disability",
                    clock.initial_ticks_to_disability
                ))
            )
            |then>> returnly(lambda clock: (setattr |to| clock)(
                "ticks_to_disability",
                clock.ticks_to_disability - 1
            ))
            |then>> bool
        )
        |then>> eventually
    )
)


with_error: Callable[
    [Callable[P, ResultT]],
    Callable[P, contextual[Optional[ResultT], Optional[Exception]]]
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
        |then>> right_partial(rollbackable, contextual |to| nothing)
    )
)