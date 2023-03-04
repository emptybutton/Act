from functools import partial
from typing import Any, Callable, Iterable

from pyhandling.annotations import binder, event_for, factory_for, ResourceT, ResultT
from pyhandling.binders import close, post_partial
from pyhandling.branchers import eventually, ActionChain
from pyhandling.language import then, by, to
from pyhandling.synonyms import execute_operation, positionally_unpack_to, return_, bind
from pyhandling.tools import documenting_by, collection_with_reduced_nesting_to, ArgumentPack


def callmethod(object_: object, method_name: str, *args, **kwargs) -> Any:
    """Shortcut function to call a method on an input object."""

    return getattr(object_, method_name)(*args, **kwargs)


operation_by: Callable[[...], factory_for[Any]] = documenting_by(
    """Shortcut for post_partial(execute_operation, ...)."""
)(
    close(execute_operation, closer=post_partial)
)


event_as: binder = documenting_by(
    """Shortcut for creating an event using caring."""
)(
    partial |then>> eventually
)


collection_from: Callable[[Iterable], tuple] = documenting_by(
    """Shortcut to get collection with elements from input positional arguments."""
)(
    ArgumentPack.of |then>> (getattr |by| 'args')
)


summed_collection_from: event_for[tuple] = documenting_by(
    """
    Shortcut function for creating a collection with elements from input
    positional collections.
    """
)(
    collection_from |then>> (collection_with_reduced_nesting_to |to| 1)
)


take: Callable[[Any], factory_for[Any]] = documenting_by(
    """
    Shortcut function equivalent to eventually(partial(return_, input_resource).
    """
)(
    close(return_) |then>> eventually
)


yes: event_for[bool] = documenting_by("""Shortcut for take(True).""")(take(True))
no: event_for[bool] = documenting_by("""Shortcut for take(False).""")(take(False))


collection_unpacking_in: Callable[[factory_for[ResourceT]], Callable[[Iterable], ResourceT]]
collection_unpacking_in = documenting_by(
    """
    Decorator for unpacking the collection of the output function when it is
    called.
    """
)(
    unpackly |then>> left_action_binding_of(ArgumentPack |by| dict())
)


mapping_unpacking_in: Callable[[factory_for[ResourceT]], Callable[[Mapping], ResourceT]]
mapping_unpacking_in = documenting_by(
    """
    Decorator for unpacking the mapping object of the output function when it is
    called.
    """
)(
    unpackly |then>> left_action_binding_of(ArgumentPack |to| tuple())
)