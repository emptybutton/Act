from operator import attrgetter, call, eq
from typing import Callable, Any, Tuple, Optional

from pyannotating import Special, AnnotationTemplate, input_annotation

from act.annotations import dirty, R, A, B, V, C, M, G, F, W, S, Pm, FlagT, Union
from act.arguments import unpackly
from act.atomization import atomically
from act.contexting import (
    contextual, contextually, contexted, ContextualForm, saving_context,
    with_reduced_metacontext, contextualizing, to_write, to_read, of, be,
    to_context, with_context_that
)
from act.data_flow import returnly, by, to, when, break_, and_via_indexer
from act.effects import context_effect
from act.errors import ReturningError
from act.error_flow import raising
from act.flags import flag_about, nothing, Flag, pointed
from act.objects import obj
from act.operators import and_, not_
from act.partiality import will, partially
from act.pipeline import discretely, ActionChain, then, atomic_binding_by
from act.structures import tmap
from act.synonyms import on, returned
from act.tools import documenting_by, to_check, as_action, LeftCallable


__all__ = (
    "ok",
    "bad",
    "maybe",
    "optionally",
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
    "up",
    "mid",
    "down",
)


ok = contextualizing(flag_about('ok'))
bad = contextualizing(flag_about('bad', negative=True))


def _calling_skip_on(
    is_bad: Callable[Pm | Callable[Pm, R], bool],
    *,
    skipped: Callable[Callable[Pm, R], S],
) -> Callable[Pm, Callable[Callable[Pm, R] | Pm, R | S | Callable[Pm, R]]]:
    is_bad = to_check(is_bad)

    return on(
        lambda *args, **kwargs: (
            any(is_bad(args) for arg in args)
            or any(is_bad(arg) for arg in kwargs.values())
        ),
        skipped,
        else_=lambda action: (
            action if is_bad(action) else action(*args, **kwargs)
        ),
    )


@obj.of
class maybe:
    __call__ = discretely(on |to| not_(of(bad)))
    call_by = _calling_skip_on(
        of(bad),
        skipped=atomically(be(+bad) |then>> unpackly(contextually)),
    )


@obj.of
class optionally:
    __call__ = discretely(on |to| not_(None))
    call_by = _calling_skip_on(None, skipped=to(None))


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
    value: ContextualForm[A, Special[Exception | Flag[Exception], C]],
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

    return discretely(atomic_binding_by(... |then>> returnly(show)))(
        action_or_actions
    )


right = contextualizing(flag_about("right"))
left = contextualizing(flag_about("left", negative=True))


@and_via_indexer(lambda i: right[i] | left[i])
def either(
    *determinants_and_ways: tuple[
        Special[Callable[C, bool]],
        Special[break_, Callable[V, R] | R],
    ],
) -> LeftCallable[V | ContextualForm[V, C], contextual[R, C]]:
    """
    `when`-like function for `ContextualForm`s with determinants applied to
    contexts and implementers applied to values.

    Casts an input value to `ContextualForm`.

    For everything else see `when`.
    """

    return atomically(contexted |then>> when(*(
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
    value: V | ContextualForm[V, Flag[C] | C],
) -> contextual[V, Flag[C | contextually[Callable[..., R], future]]]:
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
        contextually[Callable[..., R], future]
        | Flag[contextually[Callable[..., R], future]]
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
    be contextualized by `do.return_` (contextualizes by calling).

    Stopping is local to a single `do` action and the executed value is
    returned without the `do.return_` flag.

    Throws `ReturningError` when trying to pass "returned value".

    `do` action is executed in the context of an empty arbitrary object that
    can be interacted with when decorating desired actions with `do.up`.

    Actions without `do.up` decoration are executed as if they were decorated
    with `saving_context |then>> do.up`.

    To write and read from context use `do.write` and `do.read` shortcuts
    instead of `to_write |then>> up` and `to_read |then>> up`.

    Contextualization is local to each `do` action: by default, you can't inject
    an arbitrary context to the top level, and the value from the `do` action is
    returned without that context (in the extracted view).

    To remove contextualization locality, call `do.openly` instead of just `do`.

    `do.openly` action will not additionally contextualize a value if it is
    already contextualized but still changes context to empty arbitrary object
    if it is `nothing`.

    `do.openly` saves the top context on return.
    """

    return_ = contextualizing(flag_about("return_"))
    up = contextualizing(flag_about('up'), to=contextually)

    write = atomically(to_write |then>> up)
    read = atomically(to_read |then>> up)

    def __call__(*lines: Special[ActionChain, Callable]) -> LeftCallable:
        return do._action_from(*lines)

    def openly(*lines: Special[ActionChain, Callable]) -> LeftCallable:
        return do._action_from(*lines, in_isolation=False)

    def _action_from(
        *lines: Special[ActionChain, Callable],
        in_isolation: bool = True,
    ) -> LeftCallable:
        lines = ActionChain((map |by| lines)(
            discretely(
                saving_context(on |to| not_(of(do.return_)))
                |then>> on(not_(of(do.up)), saving_context(saving_context))
                |then>> attrgetter("value")
            )
            |then>> atomically
        ))

        return atomically(
            on(
                lambda v: of(do.return_, v) or of(do.return_, contexted(v).value),
                raising(ReturningError("externally returned value")),
            )
            |then>> on(to(in_isolation), contextual)
            |then>> to_context(on(nothing, obj()))
            |then>> (lines[:-1] >= discretely((lambda line: lambda value: (
                result
                if of(do.return_, (result := line(value)).value)
                else value
            ))))
            |then>> (returned if len(lines) == 0 else lines[-1])
            |then>> saving_context(on(of(do.return_), attrgetter("value")))
            |then>> on(
                to(in_isolation),
                attrgetter("value"),
                else_=to_context(on(obj(), nothing)),
            )
        )


up: LeftCallable[
    Union[
        Callable[
            Callable[A, ContextualForm[B, C]],
            Callable[M, ContextualForm[Special[ContextualForm[V, G]], F]]
        ],
        ActionChain[Callable[
            Callable[A, ContextualForm[B, C]],
            Callable[M, ContextualForm[Special[ContextualForm[V, G], W], F]]]
        ],
    ],
    LeftCallable[
        Callable[A, ContextualForm[B, C]],
        LeftCallable[M, contextual[V | W, F | G]]
    ],
]
up = documenting_by(
    """Decorator for execution contextualization with metacontext join."""
)(discretely(atomic_binding_by(
    ...
    |then>> atomic_binding_by(... |then>> with_reduced_metacontext)
)))


mid = documenting_by(
    """Decorator for execution contextualization with metacontext removing."""
)(discretely(atomic_binding_by(
    ...
    |then>> atomic_binding_by(... |then>> contexted |then>> attrgetter("value"))
)))


down = documenting_by(
    """
    Decorator isolating a nested execution context from an outer context
    execution.
    """
)(
    atomic_binding_by(
        ...
        |then>> saving_context
        |then>> atomic_binding_by(
            contextual |then>> ... |then>> attrgetter("value")
        )
    )
    |then>> discretely
)
