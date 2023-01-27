from functools import partial
from typing import Any, Callable, Iterable

from pyhandling.annotations import binder, event_for, factory_for, handler, decorator
from pyhandling.binders import close
from pyhandling.branchers import eventually, ActionChain
from pyhandling.language import then, by, of
from pyhandling.synonyms import positionally_unpack_to, return_, bind
from pyhandling.tools import documenting_by, collection_with_reduced_nesting_to, ArgumentPack


def call_method(object_: object, method_name: str, *args, **kwargs) -> Any:
    """Shortcut function to call a method on an input object."""

    return getattr(object_, method_name)(*args, **kwargs)


event_as: binder = documenting_by(
    """Shortcut for creating an event using caring."""
)(
    partial |then>> eventually
)


collection_from: Callable[[Iterable], tuple] = documenting_by(
    """Shortcut to get collection with elements from input positional arguments."""
)(
    ArgumentPack.create_via_call |then>> (getattr |by| 'args')
)


summed_collection_from: event_for[tuple] = documenting_by(
    """
    Shortcut function for creating a collection with elements from input
    positional collections.
    """
)(
    collection_from |then>> (collection_with_reduced_nesting_to |of| 1)
)


take: Callable[[Any], factory_for[Any]] = documenting_by(
    """
    Shortcut function equivalent to eventually(partial(return_, input_resource).
    """
)(
    close(return_) |then>> eventually
)


previous_action_decorator_of: Callable[[handler], decorator] = documenting_by(
    """
    Creates a decorator that adds a action before an input function.

    Shortcut for ActionChain(...).clone_with.
    """
)(
    ActionChain |then>> (getattr |by| "clone_with")
)


next_action_decorator_of: Callable[[Callable], decorator] = documenting_by(
    """
    Creates a decorator that adds a post action to the function.

    Shortcut for partial(ActionChain(...).clone_with, is_other_handlers_left=True).
    """
)(
    previous_action_decorator_of |then>> (bind |by* ("is_other_handlers_left", True))
)


yes: event_for[bool] = documenting_by("""Shortcut for take(True).""")(take(True))
no: event_for[bool] = documenting_by("""Shortcut for take(False).""")(take(False))