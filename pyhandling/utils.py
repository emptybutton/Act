from functools import wraps, partial
from typing import Callable, Iterable

from pyhandling.annotations import Handler, handler_of, event_for
from pyhandling.branchers import ActionChain, returnly, then, mergely, eventually, on_condition
from pyhandling.binders import close, post_partial
from pyhandling.synonyms import setattr_of, return_, execute_operation, getattr_of
from pyhandling.tools import Clock


def showly(handler: Handler, *, writer: handler_of[str] = print) -> ActionChain:
    """
    Decorator function for visualizing the outcomes of intermediate stages of a
    chain of actions, or simply the input and output results of a regular handler.
    """

    writer = returnly(str |then>> writer)

    return (
        handler.clone_with_intermediate(writer, is_on_input=True, is_on_output=True)
        if isinstance(handler, ActionChain)
        else wraps(handler)(writer |then>> handler |then>> writer)
    )


documenting_by: Callable[[str], Callable[[object], object]] = (
    mergely(
        eventually(partial(return_, close(returnly(setattr_of)))),
        attribute_name=eventually(partial(return_, '__doc__')),
        attribute_value=return_
    )
)
documenting_by.__doc__ = (
    """
    Function of getting other function that getting resource with the input 
    documentation from this first function.
    """
)


as_collection: Callable[[any], tuple] = documenting_by(
    """
    Function to convert an input resource into a tuple collection.
    With a non-iterable resource, wraps it in a tuple.
    """
)(
    on_condition(
        post_partial(isinstance, Iterable),
        tuple,
        else_=lambda resource: (resource, )
    )
)


times: Callable[[int], event_for[bool]] = documenting_by(
    """
    Function to create a dirty function that will return True the input value
    (for this function) number of times, then False once after the input count
    has passed, True again n times, and so on.
    """
)(
    post_partial(execute_operation, '+', 1)
    |then>> Clock
    |then>> close(
        returnly(on_condition(
            lambda clock: not clock,
            mergely(
                close(setattr_of),
                eventually(partial(return_, 'ticks_to_disability')),
                post_partial(getattr_of, 'initial_ticks_to_disability')
            ),
            else_=return_
        ))
        |then>> returnly(
            mergely(
                close(setattr_of),
                eventually(partial(return_, 'ticks_to_disability')),
                (
                    post_partial(getattr_of, 'ticks_to_disability')
                    |then>> post_partial(execute_operation, '-', 1)
                )
            )
        )
        |then>> bool
    )
)