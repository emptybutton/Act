from datetime import datetime
from functools import wraps, partial
from math import inf
from typing import NamedTuple, Generic, Iterable, Tuple, Callable, Any, Mapping, Type, NoReturn, Optional

from pyannotating import many_or_one, AnnotationTemplate, input_annotation, Special

from pyhandling.annotations import atomic_action, dirty, handler_of, ValueT, ContextT, ResultT, checker_of, ErrorT, action_for, merger_of, ArgumentsT, reformer_of
from pyhandling.binders import returnly, closed, post_partial, eventually, unpackly
from pyhandling.branchers import ActionChain, on_condition, rollbackable, mergely, mapping_to_chain_of, mapping_to_chain
from pyhandling.language import then, by, to
from pyhandling.synonyms import execute_operation, returned, transform, raise_
from pyhandling.tools import documenting_by, in_collection, ArgumentPack, Clock, nothing, Flag


__all__ = (
    "ContextRoot", "Logger", "showly", "callmethod", "with_result",
    "operation_by", "operation_of", "shown", "binding_by", "bind", "on", "taken",
    "as_collection", "yes", "no", "times", "monadically",
    "mapping_to_chain_among", "calculation_contextualizing_over",
    "saving_context", "for_context", "contextual", "bad", "maybe", "with_error",
    "until_error", "map_", "zip_", "filter_"
)


class ContextRoot(NamedTuple, Generic[ValueT, ContextT]):
    """Class for annotating a value with some context."""

    value: ValueT
    context: ContextT

    def __repr__(self) -> str:
        return f"{self.value} when {self.context}"

    @classmethod
    def like(cls, value_and_context: tuple[ValueT, ContextT]) -> Self:
        """Class method to create from an unstructured collection."""

        value, context = value_and_context

        return cls(value, context)







def showly(
    action_or_actions: many_or_one[atomic_action],
    *,
    writer: dirty[handler_of[str]] = print
) -> dirty[ActionChain]:
    """
    Decorator function to render the results of a function or `ActionChain`
    nodes.
    """


    return monadically(bind |by| returnly(str |then>> writer))(action_or_actions)


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
    closed(execute_operation, close=post_partial)
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


shown: dirty[reformer_of[ValueT]]
shown = documenting_by("""Shortcut function for `returnly(print)`.""")(
    returnly(print)
)


def binding_by(template: Iterable[Callable | Ellipsis]) -> Callable[[Callable], ActionChain]:
    """
    Function to create a function by insertion its input function in the input
    template.

    The created function replaces `...` with an input action.
    """

    def insert_to_template(intercalary_action: Callable) -> ActionChain:
        """
        Function given as a result of calling `binding_by`. See `binding_by` for
        more info.
        """

        return ActionChain(
            intercalary_action if action is Ellipsis else action
            for action in template
        )

    return insert_to_template


def bind(
    first_node: Callable[[*ArgumentsT], ValueT],
    second_node: Callable[[ValueT], ResultT]
) -> Callable[[*ArgumentsT], ResultT]:
    """Function of binding two input functions into a sequential `ActionChain`."""

    return first_node |then>> second_node


taken: Callable[[ValueT], action_for[ValueT]] = documenting_by(
    """Shortcut function for `eventually(returned, ...)`."""
)(
    closed(returned) |then>> eventually
)


as_collection: Callable[[many_or_one[ValueT]], Tuple[ValueT]]
as_collection = documenting_by(
    """
    Function to convert an input value into a tuple collection.
    With a non-iterable value, wraps it in a tuple.
    """
)(
    on(isinstance |by| Iterable, tuple, else_=in_collection)
)


yes: action_for[bool] = documenting_by("""Shortcut for `taken(True)`.""")(taken(True))
no: action_for[bool] = documenting_by("""Shortcut for `taken(False)`.""")(taken(False))


inversion_of: Callable[[handler_of[ValueT]], checker_of[ValueT]]
inversion_of = documenting_by("""Negation adding function.""")(
    binding_by(... |then>> (transform |by| 'not'))
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
        on(
            transform |by| 'not',
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


monadically: Callable[
    [Callable[[atomic_action], reformer_of[ValueT]]],
    mapping_to_chain_of[reformer_of[ValueT]]
]
monadically = documenting_by(
    """
    Function for decorator to map actions of a certain sequence (or just one
    action) into a chain of transformations of a certain type.

    Maps actions by an input decorator one at a time.
    """
)(
    closed(map)
    |then>> binding_by(as_collection |then>> ... |then>> ActionChain)
)


mapping_to_chain_among = AnnotationTemplate(mapping_to_chain_of, [
    AnnotationTemplate(reformer_of, [input_annotation])
])


calculation_contextualizing_over = AnnotationTemplate(mapping_to_chain_among, [
        AnnotationTemplate(ContextRoot, [Any, input_annotation])
    ]
)

saving_context: calculation_contextualizing_over[ContextT] = documenting_by(
    """
    Function that represents a chain of actions (or just an action) in the form
    of operations on a value from `ContextRoot` with preservation of its
    context.
    """
)(
    monadically(lambda node: lambda root: ContextRoot(
        node(root.value), root.context
    ))
)


for_context: mapping_to_chain_among[ContextRoot[ValueT, Any]] = documenting_by(
    """
    Function that represents a chain of actions (or just an action) in the form
    of operations on a context from `ContextRoot` with preservation of its
    value.
    """
)(
    monadically(lambda node: lambda root: ContextRoot(
        root.value, node(root.context)
    ))
)


contextual: Callable[[ValueT], ContextRoot[ValueT, None]]
contextual = documenting_by(
    """
    Function representing the input value as a value with a context (which
    is `nothing`).
    """
)(
    ContextRoot |by| nothing
)


bad = Flag('bad', sign=False)


maybe: calculation_contextualizing_over[Special[bad]]
maybe = documenting_by(
    """
    Action or action chain transformation function.

    Stop a `ContextRoot` value action chain on a node that returned
    'bad' flag.

    Skips calculation of `ContextRoot` values when context is `bad`.
    """
)(
    monadically(lambda node: lambda root: (
        root.value >= node |then>> on(
            operation_by('is', bad),
            taken(ContextRoot(root.value, bad)),
            else_=ContextRoot |by| root.context,
        )
        if root.context is not bad
        else root
    ))
)


with_error: Callable[
    [Callable[[*ArgumentsT], ResultT]],
    Callable[[*ArgumentsT], ContextRoot[Optional[ResultT], Optional[Exception]]]
]
with_error = documenting_by(
    """
    Decorator that causes the decorated function to return the error that
    occurred.

    Returns in `ContextRoot` format (result, error).
    """
)(
    binding_by(... |then>> contextual)
    |then>> post_partial(rollbackable, ContextRoot |to| nothing)
)


until_error: calculation_contextualizing_over[Special[Exception]]
until_error = documenting_by(
    """Function for a chain of actions with the return of an error."""
)(
    monadically(lambda node: lambda root: (
        rollbackable(
            node |then>> (ContextRoot |by| root.context),
            lambda error: ContextRoot(root.value, error),
        )(root.value)
        if not isinstance(root.context, Exception)
        else root
    ))
)


map_ = documenting_by("""`map` function returning `tuple`""")(
    partial(map |then>> tuple)
)

zip_ = documenting_by("""`zip` function returning `tuple`""")(
    partial(zip |then>> tuple)
)

filter_ = documenting_by("""`filter` function returning `tuple`""")(
    partial(filter |then>> tuple)
)
