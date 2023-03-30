from datetime import datetime
from functools import wraps, partial
from typing import NamedTuple, Generic, Iterable, Tuple, Callable, Any, Mapping, Type, NoReturn, Optional, Self

from pyannotating import many_or_one, AnnotationTemplate, input_annotation, Special

from pyhandling.annotations import atomic_action, dirty, handler_of, ValueT, ContextT, ResultT, checker_of, ErrorT, action_for, merger_of, ArgumentsT, reformer_of
from pyhandling.binders import returnly, closed, post_partial, eventually, unpackly
from pyhandling.branchers import ActionChain, on, rollbackable, mergely, mapping_to_chain_of, mapping_to_chain
from pyhandling.language import then, by, to
from pyhandling.synonyms import execute_operation, returned, transform, raise_
from pyhandling.tools import documenting_by, in_collection, ArgumentPack, Clock, nothing, Flag


__all__ = (
    "ContextRoot", "context_oriented", "atomically", "showly", "callmethod",
    "with_result", "operation_by", "operation_of", "shown", "binding_by", "bind",
    "taken", "as_collection", "yes", "no", "times", "monadically",
    "mapping_to_chain_among", "execution_context_when", "saving_context",
    "contextual", "bad", "maybe", "with_error", "until_error", "map_", "zip_",
    "filter_"
)


class atomically:
    """
    Decorator that removes the behavior of an input action, leaving only
    calling.
    """

    def __init__(self, action: action_for[ResultT]):
        self._action = action

    def __repr__(self) -> str:
        return f"atomically({self._action})"

    def __call__(self, *args, **kwargs) -> ResultT:
        return self._action(*args, **kwargs)


class _Fork(NamedTuple, Generic[ValueT, ResultT]):
    """NamedTuple to store an action to execute on a condition."""

    checker: Callable[[*ArgumentsT], bool]
    action: Callable[[*ArgumentsT], ResultT]


def branching(
    *forks: tuple[
        Callable[[*ArgumentsT], bool],
        Callable[[*ArgumentsT], ResultT],
    ],
    else_: Callable[[*ArgumentsT], ResultT] = returned,
) -> Callable[[*ArgumentsT], ResultT]:
    """
    Function for using action branching like `if`, `elif` and `else` statements.

    With default `else_` takes actions of one value.
    """

    forks = map_(_Fork, forks)

    return (
        on(*forks[0], else_=else_)
        if len(forks) == 1
        else on(forks[0].checker, forks[0].action, else_=branching(*forks[1:]))
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


map_ = documenting_by("""`map` function returning `tuple`""")(
    atomically(map |then>> tuple)
)


zip_ = documenting_by("""`zip` function returning `tuple`""")(
    atomically(zip |then>> tuple)
)


filter_ = documenting_by("""`filter` function returning `tuple`""")(
    atomically(filter |then>> tuple)
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


monadically: Callable[
    [Callable[[one_value_action], reformer_of[ValueT]]],
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


execution_context_when = AnnotationTemplate(mapping_to_chain_among, [
        AnnotationTemplate(ContextRoot, [Any, input_annotation])
    ]
)


saving_context: execution_context_when[ContextT] = documenting_by(
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


bad = Flag('bad', sign=False)


maybe: execution_context_when[Special[bad]]
maybe = documenting_by(
    """
    Action execution context that stops the thread of execution When the `bad`
    flag returns.

    When stopped, returns the previous value calculated before the `bad` flag in
    context with `bad` flag.
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


until_error: execution_context_when[Special[Exception]]
until_error = documenting_by(
    """
    Action execution context that stops the thread of execution when an error
    occurs.

    When skipping, it saves the last validly calculated value and an occurred
    error as context.
    """
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


def showly(
    action_or_actions: many_or_one[one_value_action],
    *,
    show: dirty[one_value_action] = print,
) -> dirty[ActionChain]:
    """
    Action executing context with the effect of writing results.
    Prints results by default.
    """

    return monadically(binding_by(... |then>> returnly(show)))(
        action_or_actions
    )


writing = Flag("writing")
reading = Flag("writing")


_ReadingResultT = TypeVar("_ReadingResultT")


@documenting_by(
    """
    Execution context with the ability to read and write to a context.

    Writes to context by contextual node with `writing` context and reads value
    from context by contextual node with `reading` context.

    Before interacting with a context, the last calculated result must come to
    contextual nodes, after a context itself.

    When writing to a context, result of a contextual node will be a result
    calculated before it, and when reading, a result of reading.
    """
)
@monadically
@closed
def considering_context(
    node: Callable[[ValueT], ResultT] | ContextRoot[
        Callable[[ValueT], reformer_of[ContextT]] | Callable[[ValueT], Callable[[ContextT], _ReadingResultT]],
        Special[writing | reading]
    ],
    root: ContextRoot[ValueT, ContextT]
) -> ContextRoot[ResultT | _ReadingResultT, ContextT]:
    if isinstance(node, ContextRoot):
        if node.context is writing:
            return ContextRoot(root.value, node.value(root.value)(root.context))

        if node.context is reading:
            return ContextRoot(node.value(root.value)(root.context), root.context)

    return saving_context(node)(root)