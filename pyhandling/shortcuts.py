from functools import partial
from typing import Any, Callable, Iterable

from pyhandling.annotations import binder, event_for, factory_for, handler, decorator
from pyhandling.binders import close
from pyhandling.branchers import eventually, ActionChain
from pyhandling.language import then, by, of
from pyhandling.synonyms import positionally_unpack_to, return_, bind
from pyhandling.tools import documenting_by, collection_with_reduced_nesting_to, ArgumentPack




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
