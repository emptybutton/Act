from datetime import datetime
from functools import wraps, partial
from math import inf
from typing import Iterable, Tuple, Callable, Any, Mapping, Type, NoReturn

from pyannotating import many_or_one, AnnotationTemplate, input_annotation, Special

from pyhandling.annotations import atomic_action, dirty, handler_of, ResourceT, ResultT, checker_of, ErrorT, action_for, merger_of, ArgumentsT, reformer_of
from pyhandling.binders import returnly, closed, post_partial, eventually, unpackly
from pyhandling.branchers import ActionChain, on_condition, chain_constructor, rollbackable, mapping_for_chain_among
from pyhandling.language import then, by, to
from pyhandling.error_controllers import BadResourceWrapper, ResourceWithError, bad_wrapped_or_not
from pyhandling.synonyms import execute_operation, returned, transform, raise_
from pyhandling.tools import documenting_by, in_collection, ArgumentPack, Clock


__all__ = (
    "Logger", "showly", "callmethod", "with_result",
    "operation_by", "operation_of", "shown", "action_inserting_in",
    "left_action_binding_of", "action_binding_of", "taken", "as_collection",
    "collection_from", "collection_unpacking_in", "keyword_unpacking_in",
    "yes", "no", "times", "becoming_skipping_on", "optional_raising_of", "monadically",
    "monada_among", "maybe", "optional_bad_resource_from",
    "bad_resource_wrapping_on", "with_error", "between_errors"
)


class Logger:
    """
    Class for logging any messages.

    Stores messages via the input value of its call.

    Has the ability to clear logs when their limit is reached, controlled by the
    `maximum_log_count` attribute and the keyword argument.

    Able to save the date of logging in the logs. Controlled by `is_date_logging`
    attribute and keyword argument.

    Suggested to be used with showly function.
    """

    def __init__(
        self,
        logs: Iterable[str] = tuple(),
        *,
        maximum_log_count: int | float = inf,
        is_date_logging: bool = False
    ):
        self._logs = list()
        self.maximum_log_count = maximum_log_count
        self.is_date_logging = is_date_logging

        for log in logs:
            self(log)

    @property
    def logs(self) -> Tuple[str]:
        return tuple(self._logs)

    def __call__(self, message: str) -> None:
        self._logs.append(
            message
            if not self.is_date_logging
            else f"[{datetime.now()}] {message}"
        )

        if len(self._logs) > self.maximum_log_count:
            self._logs = self._logs[self.maximum_log_count:]


def showly(
    action_resource: many_or_one[atomic_action],
    *,
    writer: dirty[handler_of[str]] = print
) -> dirty[ActionChain]:
    """
    Decorator function to render the results of a function or `ActionChain`
    nodes.
    """

    return monadically(action_binding_of(returnly(str |then>> writer)))(
        action_resource
    )


def with_result(
    result: ResultT,
    action: Callable[[*ArgumentsT], Any]
) -> Callable[[*ArgumentsT], ResultT]:
    """Function to force an input result for an input action."""

    return action |then>> taken(result)


def callmethod(object_: object, method_name: str, *args, **kwargs) -> Any:
    """Shortcut function to call a method on an input object."""

    return getattr(object_, method_name)(*args, **kwargs)


operation_by: action_for[action_for[Any]] = documenting_by(
    """Shortcut for `post_partial(execute_operation, ...)`."""
)(
    closed(execute_operation, closer=post_partial)
)


operation_of: Callable[[str], merger_of[Any]] = documenting_by(
    """
    Function to get the operation of the string representation of some syntax
    operator between two elements.
    """
)(
    lambda operator: lambda fitst_operand, second_operand: execute_operation(
        fitst_operand,
        operator,
        second_operand
    )
)


shown: dirty[reformer_of[ResourceT]]
shown = documenting_by("""Shortcut function for `returnly(print)`.""")(
    returnly(print)
)


def action_inserting_in(
    action_template: Iterable[Callable | Ellipsis]
) -> Callable[[Callable], ActionChain]:
    """
    Function to create a function by insertion its input function in the input
    template.

    The created function replaces `...` with an input action.
    """

    def insert_to_template(intercalary_action: Callable) -> ActionChain:
        """
        Function given as a result of calling `action_inserting_in`.
        See `action_inserting_in` for more info.
        """

        return ActionChain(
            intercalary_action if action is Ellipsis else action
            for action in action_template
        )

    return insert_to_template


left_action_binding_of: Callable[
    [Callable[[*ArgumentsT], ResourceT]],
    Callable[[Callable[[ResourceT], ResultT]], Callable[[*ArgumentsT], ResultT]]
]
left_action_binding_of = documenting_by(
    """Creates a decorator that adds a action before an input function."""
)(
    lambda first_node: lambda second_node: ActionChain((first_node, second_node))
)


action_binding_of: Callable[
    [Callable[[ResourceT], ResultT]],
    Callable[[Callable[[*ArgumentsT], ResourceT]], Callable[[*ArgumentsT], ResultT]]
]
action_binding_of = documenting_by(
    """Creates a decorator that adds a post action to the function."""
)(
    lambda second_node: lambda first_node: ActionChain((first_node, second_node))
)


taken: Callable[[ResourceT], action_for[ResourceT]] = documenting_by(
    """Shortcut function for `eventually(returned, ...)`."""
)(
    closed(returned) |then>> eventually
)


as_collection: Callable[[many_or_one[ResourceT]], Tuple[ResourceT]]
as_collection = documenting_by(
    """
    Function to convert an input resource into a tuple collection.
    With a non-iterable resource, wraps it in a tuple.
    """
)(
    on_condition(isinstance |by| Iterable, tuple, else_=in_collection)
)


collection_from: Callable[[*ArgumentsT], tuple[*ArgumentsT]] = documenting_by(
    """Shortcut to get collection with elements from input positional arguments."""
)(
    ArgumentPack.of |then>> (getattr |by| 'args')
)


collection_unpacking_in: Callable[[action_for[ResourceT]], Callable[[Iterable], ResourceT]]
collection_unpacking_in = documenting_by(
    """
    Decorator for unpacking the collection of the output function when it is
    called.
    """
)(
    unpackly |then>> left_action_binding_of(ArgumentPack |by| dict())
)


keyword_unpacking_in: Callable[[action_for[ResourceT]], Callable[[Mapping], ResourceT]]
keyword_unpacking_in = documenting_by(
    """
    Decorator for unpacking the mapping object of the output function when it is
    called.
    """
)(
    unpackly |then>> left_action_binding_of(ArgumentPack |to| tuple())
)


yes: action_for[bool] = documenting_by("""Shortcut for `taken(True)`.""")(taken(True))
no: action_for[bool] = documenting_by("""Shortcut for `taken(False)`.""")(taken(False))


inversion_of: Callable[[handler_of[ResourceT]], checker_of[ResourceT]]
inversion_of = documenting_by("""Negation adding function.""")(
    action_binding_of(transform |by| 'not')
)


times: Callable[[int], dirty[action_for[bool]]] = documenting_by(
    """
    Function to create a function that will return `True` the input value (for
    this function) number of times, then `False` once after the input count has
    passed, `True` again n times, and so on.

    Resulting function is independent of its input arguments.
    """
)(
    operation_by('+', 1)
    |then>> Clock
    |then>> closed(
        (on_condition |then>> returnly)(
            transform |by| 'not',
            lambda clock: (setattr |to| clock)(
                "ticks_to_disability",
                clock.initial_ticks_to_disability
            )
        )
        |then>> returnly(lambda clock: (setattr |to| clock)(
            "ticks_to_disability",
            clock.ticks_to_disability - 1
        ))
        |then>> bool
    )
    |then>> eventually
)


becoming_skipping_on: Callable[
    [checker_of[ResourceT]],
    Callable[
        [Callable[[ResourceT], ResultT]],
        Callable[[ResourceT], ResultT | ResourceT]
    ]
]
becoming_skipping_on = documenting_by(
    """
    Function for creating a decorator for an action, when calling which it may
    not be explored if the conditions of the input (for this function) checker
    to the input argument of the decorated action are true.
    """
)(
    inversion_of |then>> closed(partial(on_condition, else_=returned))
)


optional_raising_of: Callable[
    [Type[ErrorT]],
    Callable[[ErrorT | ResourceT], NoReturn | ResourceT]
]
optional_raising_of = documenting_by(
    """
    Function that selectively raises an error (the type of which is the input,
    respectively).

    When called with another resource, returns it.
    """
)(
    closed(isinstance, closer=post_partial)
    |then>> post_partial(on_condition, raise_, else_=returned)
)


monadically: Callable[
    [Callable[[atomic_action], reformer_of[ResourceT]]],
    Callable[[many_or_one[atomic_action]], ActionChain[reformer_of[ResourceT]]]
]
monadically = documenting_by(
    """
    Function for decorator to map actions of a certain sequence (or just one
    action) into a chain of transformations of a certain type.

    Maps actions by an input decorator one at a time.
    """
)(
    closed(map)
    |then>> action_inserting_in(as_collection |then>> ... |then>> ActionChain)
)


monada_among = (AnnotationTemplate |to| mapping_for_chain_among)([
    AnnotationTemplate(reformer_of, [input_annotation])
])


with_context_saving: monada_among[ResourceWithContext] = documenting_by(
    """
    Function that represents a chain of actions (or just an action) in the form
    of operations on a resource from `ResourceWithContext` with preservation of
    its context.
    """
)(
    monadically(lambda node: lambda contextual: ResourceWithContext(
        node(contextual.resource),
        contextual.context,
    ))
)


def for_context(
    context_handler: Callable[[ContextT], ResultT],
    contextual: ResourceWithContext[Any, ContextT],
) -> ResultT:
    return context_handler(contextual.context)


in_context: Callable[[ResourceT], ResourceWithContext[ResourceT, None]]
in_context = documenting_by(
    """
    Function representing the input resource as a resource with a context (which
    is None).
    """
)(
    ResourceWithContext |by| None
)


def wrapping_with_context_on(
    is_valid_to_wrap: checker_of[ResourceT],
    *,
    context_from: Callable[[ResourceT], ContextT] = taken(None),
) -> ResourceT | ResourceWithContext[ResourceT, ContextT]:
    """
    Function for the function of optionally wrapping the input resource in 
    `ResourceWithContext`.
    """

    return on_condition(
        is_valid_to_wrap,
        mergely(taken(ResourceWithContext), returned, context_from),
        else_=returned,
    )


bad_resource_wrapping_on: Callable[
    [checker_of[ResourceT]],
    Callable[[ResourceT], bad_wrapped_or_not[ResourceT]]
]
bad_resource_wrapping_on = documenting_by(
    """
    Function for optional wrapping in BadResourceWrapper under the conditions
    given by the input checker.

    The output function returns the input resource when the checker condition
    is negative.
    """
)(
    post_partial(on_condition, BadResourceWrapper, else_=returned)
)


bad_resource_context = Flag("bad_resource_context")


maybe: monada_among[ResourceWithContext[Any, Special[bad_resource_context]]]
maybe = documenting_by(
    """
    Function to finish execution of an action chain when a bad resource keeper
    appears in it by returning this same keeper, skipping subsequent action
    chain nodes.
    """
)(
    with_context_saving |then>> monadically(
        becoming_skipping_on(for_context(operation_by('is', bad_resource_context)))
    )
)


with_error: Callable[
    [Callable[[*ArgumentsT], ResultT]],
    Callable[[*ArgumentsT], ResourceWithContext[ResultT, Exception]]
]
with_error = documenting_by(
    """
    Decorator that causes the decorated function to return the error that
    occurred.

    Returns in `ResourceWithContext` format (result, error).
    """
)(
    action_binding_of(lambda result: ResourceWithContext(result, None))
    |then>> (rollbackable |by| (lambda error: ResourceWithContext(None, error)))
)


between_errors: mapping_for_chain_among[Callable[[Special[ResourceWithContext]], ResourceWithContext]]
between_errors = documenting_by(
    """Function for a chain of actions with the return of an error."""
)(
    monadically(
        with_error
        |then>> left_action_binding_of(on_condition(
            isinstance |by| ResourceWithContext, getattr |by| "resource", else_=returned
        ))
        |then>> becoming_skipping_on(
            lambda resource: isinstance(resource, ResourceWithError) and resource.error is not None
        )
    )
)