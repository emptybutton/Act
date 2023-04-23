from operator import attrgetter, eq, pos, call
from typing import Callable, Any, TypeVar, Tuple

from pyannotating import (
    many_or_one, AnnotationTemplate, input_annotation, Special
)

from pyhandling.annotations import (
    one_value_action, dirty, ValueT, ContextT, ResultT, reformer_of,
    checker_of, event_for, PointT
)
from pyhandling.atoming import atomically
from pyhandling.branching import (
    ActionChain, mapping_to_chain_of, binding_by, branching, then
)
from pyhandling.contexting import (
    contextual, contextually, contexted, context_oriented, ContextRoot
)
from pyhandling.data_flow import returnly, eventually, by, to
from pyhandling.flags import flag, nothing, Flag, pointed, pointed_or
from pyhandling.partials import will, fragmentarily
from pyhandling.structure_management import in_collection, as_collection, tmap
from pyhandling.synonyms import raise_, trying_to, on
from pyhandling.tools import documenting_by, to_check
from pyhandling.utils import isnt


__all__ = (
    "monadically",
    "mapping_to_chain_among",
    "execution_context_when",
    "native_execution_context_when",
    "saving_context",
    "to_context",
    "bad",
    "maybe",
    "until_error",
    "showly",
    "writing",
    "reading",
    "considering_context",
    "right",
    "left",
    "either",
    "future",
    "in_future",
    "future_from",
    "to_points",
    "to_value_points",
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
    atomically(
        will(map)
        |then>> binding_by(
            on(isnt(isinstance |by| ActionChain), in_collection, else_=as_collection)
            |then>> ...
            |then>> ActionChain
        )
        |then>> atomically
    )
)


mapping_to_chain_among = AnnotationTemplate(mapping_to_chain_of, [
    AnnotationTemplate(reformer_of, [input_annotation])
])


execution_context_when = AnnotationTemplate(mapping_to_chain_among, [
    AnnotationTemplate(contextual, [Any, input_annotation])
])


native_execution_context_when = AnnotationTemplate(mapping_to_chain_of, [
    AnnotationTemplate(Callable, [
        [Any],
        AnnotationTemplate(contextual, [Any, input_annotation])
    ])
])


saving_context: mapping_to_chain_of[Callable[
    [ContextRoot[ValueT, ContextT]],
    ContextRoot[Any, ContextT],
]]
saving_context = documenting_by(
    """Execution context without effect."""
)(
    monadically(lambda action: lambda root: contextual(
        action(root.value), when=root.context
    ))
)


to_context: mapping_to_chain_of[Callable[
    [ContextRoot[ValueT, ContextT]],
    ContextRoot[ValueT, Any],
]]
to_context = documenting_by(
    """Execution context for context value context calculations."""
)(
    saving_context
    |then>> binding_by(context_oriented |then>> ... |then>> context_oriented)
)


bad = flag('bad', sign=False)


maybe: native_execution_context_when[Special[bad]]
maybe = documenting_by(
    """
    The execution context that stops a thread of execution when a value is None
    or returned in the `bad` context.
    """
)(
    monadically(lambda action: contexted |then>> (lambda root: (
        root.value >= action |then>> contexted |then>> on(
            attrgetter("context") |then>> (eq |to| bad),
            contexted |by| +pointed(root.context),
            else_=attrgetter("value") |then>> (contextual |by| root.context),
        )
        if root.value is not None and root.context != bad
        else root
    )))
)


until_error: native_execution_context_when[Special[Exception | Flag[Exception]]]
until_error = documenting_by(
    """
    Execution context that stops the thread of execution when an error occurs.

    When skipping, it saves the last validly calculated value and a pointed
    occurred error as context.
    """
)(
    monadically(lambda action: contexted |then>> (lambda root: (
        trying_to(
            saving_context(action),
            pointed |then>> pos |then>> (contexted |to| root),
        )(root)
        if pointed(root.context).that(isinstance |by| Exception) == nothing
        else root
    )))
)


def showly(
    action_or_actions: many_or_one[one_value_action],
    *,
    show: dirty[one_value_action] = print,
) -> dirty[ActionChain]:
    """
    Executing context with the effect of writing results.
    Prints results by default.
    """

    return monadically(binding_by(... |then>> returnly(show)))(
        action_or_actions
    )


writing = flag("writing")
reading = flag("reading")


@documenting_by(
    """
    Execution context with the ability to read and write to a context.

    Writes to context by contextual node with `writing` context and reads value
    from context by contextual node with `reading` context.

    Before interacting with a context, the last calculated result must come to
    contextual nodes, after a context itself.

    When writing to a context, result of a contextual node will be a result
    calculated before it, and when reading, a result of reading.

    When specifying `writing` and `reading` contexts at the same time, writes to
    a context and continues with a result of the write.
    """
)
@monadically
@will
def considering_context(
    action: Callable[[ValueT], ResultT] | contextually[
        Callable[[ValueT], Callable[[ContextT], MappedT]]
        Special[writing | reading],
    ],
    value: ValueT | contextual[ValueT, ContextT]
) -> contextual[ResultT | ValueT | MappedT, MappedT | ContextT]:
    value_and_context = contexted(value)

    if not isinstance(action, contextually) or action.context != writing | reading:
        return saving_context(action)(value_and_context)

    value, context = value_and_context

    transformed_context = action(value)(context)

    if action.context == writing:
        context = transformed_context

    if action.context == reading:
        value = transformed_context

    return contextual(value, when=context)


right = flag("right")
left = flag('left', sign=False)


def either(
    *determinants_and_ways: tuple[
        Special[checker_of[ContextT]],
        Callable[[contextual[ValueT, ContextT]], ResultT] | ResultT,
    ],
    else_: Callable[[contextual[ValueT, ContextT]], ResultT] = eventually(
        raise_, ValueError("No condition is met")
    ),
) -> Callable[[contextual[ValueT, ContextT]], ResultT]:
    """
    Function for using action branching like `if`, `elif` and `else` statements
    over value in `ContextRoot` form.

    Accepts branches as tuples, where in the first place is the action of
    checking by a context of an input value and in the second place is the
    action that implements the logic of this condition over the value with its
    context.

    When condition checkers are not called, compares an input context with these
    check values.

    With non-callable implementations of the conditional logic, returns those
    non-callable values.

    With default `else_` throws an error about a failed comparison if none of
    the conditions are met.
    """

    return branching(
        *(
            (attrgetter("context") |then>> to_check(determinant), way)
            for determinant, way in determinants_and_ways
        ),
        else_=else_
    )


future = flag("future")


@fragmentarily
def in_future(
    action: Callable[[ValueT], ResultT],
    value: ValueT | ContextRoot[ValueT, pointed_or[ContextT]],
) -> contextual[ValueT, Flag[ContextT | contextually[event_for[ResultT], future]]]:
    """
    Decorator to delay the execution of an input action.

    When calling the resulting action on a value, contextualizes the input value
    by the sum of the flags with a partially applied version of the resulting
    action by that value in `future` context.

    This decorator can be called the resulting action on a value, by passing
    the value as the second argument.

    For safe calling of such "future" actions from context see `future_from`.
    """

    return contexted(value, +pointed(contextually(action |to| value, when=future)))


def future_from(
    value: Special[pointed_or[contextually[event_for[ResultT], future]]],
) -> Tuple[ResultT]:
    """
    Function for safe execution of actions in `future` context.

    Calls from both the normal "future" action and the sum of the flags pointing
    the "future" actions.

    Returns a tuple of the results of found actions.
    """

    return tmap(
        call,
        pointed(value).that(lambda value: (
            isinstance(value, contextually)
            and value.context == future
        )).points,
    )


to_points: mapping_to_chain_of[Callable[[pointed_or[PointT]], Flag[PointT]]]
to_points = documenting_by(
    """Execution context to execute inside `Flag.points`."""
)(
    monadically(lambda action: lambda flags: pointed(*map(
        action,
        pointed(flags).points,
    )))
)


to_value_points: mapping_to_chain_among[Flag] = documenting_by(
    """
    Flag `point` execution context of flags whose `points` do not point to
    themselves.
    """
)(
    monadically(on |to| isnt(isinstance |by| Flag)) |then>> to_points
)
