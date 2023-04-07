from operator import attrgetter
from typing import Callable, Any, TypeVar

from pyannotating import many_or_one, AnnotationTemplate, input_annotation, Special

from pyhandling.annotations import one_value_action, dirty, ValueT, ContextT, ResultT, reformer_of
from pyhandling.atoming import atomically
from pyhandling.contexting import contextual, contextually, context_pointed
from pyhandling.branching import ActionChain, on, rollbackable, mapping_to_chain_of, mapping_to_chain, binding_by
from pyhandling.data_flow import returnly
from pyhandling.flags import flag, nothing, Flag, flag_to
from pyhandling.language import then, by, to
from pyhandling.partials import closed
from pyhandling.structure_management import as_collection
from pyhandling.synonyms import returned, raise_
from pyhandling.tools import documenting_by
from pyhandling.utils import isnt


__all__ = (
    "monadically",
    "mapping_to_chain_among",
    "execution_context_when",
    "native_execution_context_when",
    "saving_context",
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
        closed(map)
        |then>> binding_by(as_collection |then>> ... |then>> ActionChain)
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


saving_context: execution_context_when[ContextT] = documenting_by(
    """Execution context without effect."""
)(
    monadically(lambda node: lambda root: contextual(
        node(root.value), when=root.context
    ))
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
    monadically(lambda node: to_contextual_form(lambda root: (
        root.value >= node |then>> on(
            lambda result: context_pointed(as_contextual(result)).flag == bad,
            attrgetter("value") |then>> (contextual |by| (flag_to(root.context) | bad)),
            else_=contextual |by| root.context,
        )
        if root.context != bad
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
    monadically(lambda node: to_contextual_form(lambda root: (
        rollbackable(
            node |then>> (contextual |by| root.context),
            lambda error: contextual(root.value, when=flag_to(root.context, error)),
        )(root.value)
        if flag_to(root.context).of(isinstance |by| Exception) == nothing
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
@closed
def considering_context(
    node: Callable[[ValueT], ResultT] | contextually[
        Callable[[ValueT], Callable[[ContextT], _NewContextT]]
        | Callable[[ValueT], Callable[[ContextT], _ReadingResultT]],
        Special[writing | reading],
    ],
    root: contextual[ValueT, ContextT]
) -> contextual[ResultT | ValueT | _ReadingResultT, ContextT]:
    if isinstance(node, contextually):
        if node.context == writing:
            return contextual(root.value, node(root.value)(root.context))

        if node.context == reading:
            return contextual(node(root.value)(root.context), root.context)

    return saving_context(node)(root)


right = flag("right")
left = flag('left', sign=False)


def either(
    *context_and_action: tuple[ContextT, Callable[[contextual[ValueT, ContextT]], ResultT]],
    else_: Callable[[contextual[ValueT, ContextT]], ResultT] = returned,
) -> Callable[[contextual[ValueT, ContextT]], ResultT]:
    """Shortcut for `branching` with context checks."""

    return branching(*(
        (lambda root: root.context is context, action)
        for context, action in context_and_action
    ))



to_points: mapping_to_chain_among[Flag] = documenting_by(
    """Execution context of flag `points`."""
)(
    monadically(lambda action: lambda flags: flag_to(*map(
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
