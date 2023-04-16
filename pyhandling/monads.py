from operator import attrgetter, eq, pos
from typing import Callable, Any, TypeVar

from pyannotating import many_or_one, AnnotationTemplate, input_annotation, Special

from pyhandling.annotations import one_value_action, dirty, ValueT, ContextT, ResultT, reformer_of, checker_of
from pyhandling.atoming import atomically
from pyhandling.contexting import contextual, contextually, contexted, context_pointed
from pyhandling.branching import ActionChain, mapping_to_chain_of, mapping_to_chain, binding_by, branching
from pyhandling.data_flow import returnly, dynamically
from pyhandling.flags import flag, nothing, Flag, pointed
from pyhandling.language import then, by, to
from pyhandling.partials import will
from pyhandling.structure_management import in_collection, as_collection
from pyhandling.synonyms import returned, raise_, trying_to, on
from pyhandling.tools import documenting_by
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
    "to_points",
    "to_acyclic_points",
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
    The execution context that stops a thread of execution when a value is
    returned in the `bad` context.

    Skips execution if the input value is in a `bad` context.
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

    When skipping, it saves the last validly calculated value and an occurred
    error as context.
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


writing = flag("writing", action=lambda action: contextually(action, when=writing))
reading = flag("reading", action=lambda action: contextually(action, when=reading))


_ReadingResultT = TypeVar("_ReadingResultT")
_NewContextT = TypeVar("_NewContextT")


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
@will
def considering_context(
    action: Callable[[ValueT], ResultT] | contextually[
        Callable[[ValueT], Callable[[ContextT], _NewContextT]]
        | Callable[[ValueT], Callable[[ContextT], _ReadingResultT]],
        Special[writing | reading],
    ],
    root: contextual[ValueT, ContextT]
) -> contextual[ResultT | ValueT | _ReadingResultT, ContextT | _NewContextT]:
    root = contexted(root)

    if not isinstance(action, contextually) or action.context != writing | reading:
        return saving_context(action)(root)

    value, context = root

    transformed_context = action(value)(context)

    if action.context == writing:
        context = transformed_context

    if action.context == reading:
        value = transformed_context

    return contextual(value, when=context)


right = flag("right")
left = flag('left', sign=False)


def either(
    *context_and_actions: tuple[ContextT, Callable[[contextual[ValueT, ContextT]], ResultT]],
    else_: Callable[[contextual[ValueT, ContextT]], ResultT] = returned,
) -> Callable[[contextual[ValueT, ContextT]], ResultT]:
    """Shortcut for `branching` with context checks."""

    return branching(*(
        (lambda root: root.context == context, action)
        for context_and_action in context_and_actions
        for context, action in context_and_action
    ))



to_points: mapping_to_chain_among[Flag] = documenting_by(
    """Execution context of flag `points`."""
)(
    monadically(lambda action: lambda flags: pointed(*map(
        attrgetter("point") |then>> action,
        flags,
    )))
)


to_acyclic_points: mapping_to_chain_among[Flag] = documenting_by(
    """
    Flag `point` execution context of flags whose `points` do not point to
    themselves.
    """
)(
    monadically(on |to| isnt(isinstance |by| Flag)) |then>> to_points
)
