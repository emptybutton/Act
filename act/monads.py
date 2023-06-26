from operator import attrgetter, call, eq
from typing import Callable, Any, Tuple, Optional

from pyannotating import Special, AnnotationTemplate, input_annotation

from act.aggregates import context_effect
from act.annotations import dirty, R, checker_of, event_for, A, B, V, FlagT, C
from act.atomization import atomically
from act.contexting import (
    contextual, contextually, contexted, ContextRoot, saving_context,
    with_reduced_metacontext, contextualizing
)
from act.data_flow import returnly, by, to, matching, break_
from act.flags import flag_about, nothing, Flag, pointed
from act.objects import obj
from act.operators import and_
from act.partiality import will, partially
from act.pipeline import discretely, ActionChain, binding_by, then
from act.structures import tmap
from act.synonyms import on, returned
from act.tools import documenting_by, to_check, as_action, LeftCallable


__all__ = (
    "ok",
    "bad",
    "maybe",
    "until_error",
    "erroneous",
    "showly",
    "right",
    "left",
    "either",
    "future",
    "in_future",
    "future_from",
    "is_in_future",
    "do",
)


ok = contextualizing(flag_about('ok'))
bad = contextualizing(flag_about('bad', negative=True))


@documenting_by(
    """
    Effect to stop an execution when an input value is None or returned in the
    `bad` context.

    Atomically applied to actions in `ActionChain`.
    """
)
@context_effect(annotation_of=lambda v: (
    Optional[v] | bad[Optional[v]]
))
@discretely
@will
def maybe(
    action: Callable[A, B],
    value: contextual[
        Optional[A] | ContextRoot[V, Special[bad, Flag]],
        Special[bad, FlagT],
    ],
) -> contextual[Optional[A | B | V], Special[bad, FlagT]]:
    stored_value, context = value

    if contexted(stored_value).context == bad:
        return contexted(stored_value, +pointed(context))
    elif stored_value is None or context == bad:
        return value
    else:
        return value >= (
            saving_context(action)
            |then>> on(
                lambda result: contexted(result.value).context == bad,
                with_reduced_metacontext,
            )
        )


@documenting_by(
    """
    Effect to stop an execution when an error occurs or the presence of an
    error (or a flag pointing an error) as a context of an input value.

    When an error occurs during execution, returns an input value with a flag
    pointing its original context and an error that occurred.
    """
)
@context_effect
@discretely
@will
def until_error(
    action: Callable[A, B],
    value: ContextRoot[A, Special[Exception | Flag[Exception], C]],
) -> contextual[A | B, C | Flag[C | Exception]]:
    if pointed(value.context).that(isinstance |by| Exception) != nothing:
        return value

    try:
        return saving_context(action, value)
    except Exception as error:
        return contexted(value, +pointed(error))


erroneous = AnnotationTemplate(contextual, [
    input_annotation, Exception | Flag[Exception]
])


@dirty
@partially
def showly(
    action_or_actions: Callable[A, B] | ActionChain[Callable[A, B]],
    *,
    show: dirty[Callable[B, Any]] = print,
) -> dirty[ActionChain[Callable[[A], B]]]:
    """
    Effect of writing results of an input action or actions from an
    `ActionChain` to something. Default to console.
    """

    return discretely(binding_by(... |then>> returnly(show)))(
        action_or_actions
    )


right = contextualizing(flag_about("right"))
left = contextualizing(flag_about("left", negative=True))


def either(
    *determinants_and_ways: tuple[
        Special[checker_of[C]],
        Special[break_, Callable[V, R] | R],
    ],
) -> LeftCallable[V | ContextRoot[V, C], contextual[R, C]]:
    """
    `matching`-like function for `ContextRoots` with determinants applied to
    contexts and implementers applied to values.

    Casts an input value to `ContextRoot`.

    For everything else see `matching`.
    """

    return atomically(contexted |then>> matching(*(
        (
            (
                determinant
                if determinant is Ellipsis
                else attrgetter("context") |then>> to_check(determinant)
            ),
            way if way is break_ else saving_context(as_action(way)),
        )
        for determinant, way in determinants_and_ways
    )))


future = contextualizing(flag_about("future"), to=contextually)


@partially
def in_future(
    action: Callable[V, R],
    value: V | ContextRoot[V, Flag[C] | C],
) -> contextual[V, Flag[C | contextually[event_for[R], future]]]:
    """
    Decorator to delay the execution of an input action.

    When calling the resulting action on a value, contextualizes the input value
    by the sum of the flags with a partially applied version of the resulting
    action by that value in `future` context.

    This decorator can be called the resulting action on a value, by passing
    the value as the second argument.

    For safe calling of such "future" actions from context see `future_from`.
    """

    return contexted(
        value,
        +pointed(contextually(action |to| contexted(value).value, future)),
    )


def future_from(
    value: Special[
        contextually[event_for[R], future]
        | Flag[contextually[event_for[R], future]]
    ],
) -> Tuple[R]:
    """
    Function for safe execution of actions in `future` context.

    Calls from both the normal "future" action and the sum of the flags pointing
    the "future" actions.

    Returns a tuple of the results of found actions.
    """

    return tmap(call, pointed(value).that(is_in_future).points)


is_in_future: LeftCallable[Special[contextually[Callable, Special[future]]], bool]
is_in_future = documenting_by(
    """Function to check if an input value is a `in_future` deferred action."""
)(
    and_(
        isinstance |by| contextually,
        attrgetter("context") |then>> (eq |by| future),
    )
)


@obj.of
class do:
    """
    Execution context for multiple actions on the same value.

    To stop execution (including within one non-atomic action), the value must
    be contextualized by `do.return_`.

    Stopping is local to a single `do` action and the executed value is
    returned without the `do.return_` flag.

    With a normal `do`, unflagged `ContextRoot` value is unpacked.
    Use `do.in_form` to save the form.
    """

    return_ = contextualizing(flag_about("return_"))

    @staticmethod
    def __call__(*lines: Special[ActionChain, Callable]) -> LeftCallable:
        return do._action_from(*lines)

    def in_form(*lines: Special[ActionChain, Callable]) -> LeftCallable:
        return do._action_from(*lines, in_form=True)

    def _action_from(
        *lines: Special[ActionChain, Callable],
        in_form: bool = False,
    ) -> LeftCallable:
        lines = ActionChain((map |by| lines)(
            discretely((on |to| (lambda v: contexted(v).context != do.return_)))
            |then>> atomically
        ))

        return atomically(
            (lines[:-1] >= discretely((lambda line: lambda value: (
                result
                if contexted(result := line(value)).context == do.return_
                else value
            ))))
            |then>> (returned if len(lines) == 0 else lines[-1])
            |then>> (contexted |by| -do.return_)
            |then>> on(
                lambda v: not in_form and v.context == nothing,
                lambda v: v.value,
            )
        )
