from operator import attrgetter, call
from typing import Callable, Any, Optional

from pyannotating import Special, AnnotationTemplate, input_annotation

from act.annotations import dirty, R, A, B, V, C, M, G, F, W, P, Pm, Union
from act.atomization import func
from act.contexting import (
    contextual, contextually, contexted, ContextualForm, saving_context,
    with_reduced_metacontext, contextualizing, to_write, to_read, of, to_context,
    with_context_that
)
from act.data_flow import returnly, by, to, when, break_, and_via_indexer
from act.effects import context_effect
from act.errors import ReturningError
from act.error_flow import raising
from act.flags import flag_about, nothing, Flag, pointed, to_points
from act.objects import obj
from act.operators import not_
from act.partiality import will, partially, rpartial
from act.pipeline import discretely, ActionChain, then, atomic_binding_by
from act.synonyms import on
from act.tools import documenting_by, to_check, as_action, LeftCallable, _get


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
    "in_future",
    "parallel",
    "future",
    "has_future",
    "returned",
    "do",
    "up",
    "mid",
    "down",
)


ok = contextualizing(flag_about('ok'))
bad = contextualizing(flag_about('bad', negative=True))

maybe = documenting_by(
    """
    Decorator to stop an execution when an input value is returned with the
    `bad` context.

    Atomically applied to actions in `ActionChain`.
    """
)(
    discretely(on |to| not_(of(bad)))
)


@obj.of
class optionally:
    """
    Decorator to stop an execution when an input value is `None`.

    Atomically applied to actions in `ActionChain`.

    Use `call_by` to call with optional arguments over an optional action.
    """

    __call__ = discretely(on |to| not_(None))

    @func
    def call_by(
        *args: Union[Pm.args, None],
        **kwargs: Union[Pm.kwargs, None],
    ) -> LeftCallable[Optional[Callable[Pm, R]], Optional[R]]:
        return (
            to(None)
            if any(arg is None for arg in (*args, *kwargs.values()))
            else on(not_(None), rpartial(call, *args, **kwargs))
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
    value: ContextualForm[Special[Exception | Flag[Exception], C], A],
) -> contextual[C | Flag[C | Exception], A | B]:
    if pointed(value.context).that(isinstance |by| Exception) != nothing:
        return value

    try:
        result = saving_context(action, value)
    except Exception as error:
        result = contexted(value, +pointed(error))

    if with_context_that(isinstance |by| Exception, result.value).context != nothing:
        result = with_reduced_metacontext(result)

    return result


erroneous = AnnotationTemplate(contextual, [
    Exception | Flag[Exception], input_annotation
])


@dirty
@partially
def showly(
    action_or_actions: Callable[A, B] | ActionChain[Callable[A, B]],
    *,
    show: dirty[Callable[B, Any]] = print,
) -> dirty[ActionChain[Callable[A, B]]]:
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
) -> LeftCallable[V | ContextualForm[C, V], contextual[C, R]]:
    """
    `when`-like function for `ContextualForm`s with determinants applied to
    contexts and implementers applied to values.

    Casts an input value to `ContextualForm`.

    For everything else see `when`.
    """

    return func(contexted |then>> when(*(
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


@flag_about("in_future").to
def in_future(action: Callable[V, R]) -> LeftCallable[
    contexted[Flag[C] | C, V],
    contextual[Flag["C | in_future[Callable[..., R]]"], V],
]:
    """
    Decorator to delay the execution of an input action.

    When calling the resulting action on a value, contextualizes the input value
    by the sum of the flags with a partially applied version of the resulting
    action by that value in `future` context.

    This decorator can be called the resulting action on a value, by passing
    the value as the second argument.

    For safe calling of such "future" actions from context see `future_from`.
    """

    @func
    def future_action(value: contexted[Flag[C] | C, V]) -> contextual[
        Flag[C | in_future[Callable[..., R]]],
        V,
    ]:
        return contexted(
            value,
            +pointed(contextually(in_future, action |to| contexted(value).value)),
        )

    return future_action


parallel = contextualizing(flag_about("parallel"))


def future(
    value: contexted[
        Special[pointed[in_future[Callable[[], P]]]],
        V,
    ],
) -> contextual[Flag[Special[parallel[P]]], V]:
    """
    Function for safe execution of actions in `future` context.

    Calls from both the normal "future" action and the sum of the flags pointing
    the "future" actions.

    Returns a tuple of the results of found actions.
    """

    actions_to_future = pointed(contexted(value).context).that(of(in_future))

    return contexted(
        value,
        -actions_to_future & +to_points(call |then>> parallel, actions_to_future),
    )


def has_future(
    value: Special[ContextualForm[pointed[in_future[Callable]], Any]],
) -> bool:
    """
    Function to check for the presence of alternative input value processing
    variations.
    """

    return pointed(contexted(value).context).that(of(in_future)) != nothing


returned = contextualizing(flag_about("returned"))


@obj.of
class do:
    """
    Execution context for multiple actions on the same value.

    To stop execution (including within one non-atomic action), the value must
    be contextualized by `returned` (contextualizes by calling).

    Stopping is local to a single `do` action and the executed value is
    returned without the `returned` flag.

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
                saving_context(on |to| not_(of(returned)))
                |then>> on(not_(of(do.up)), saving_context(saving_context))
                |then>> attrgetter("value")
            )
            |then>> func
        ))

        return func(
            on(
                lambda v: of(returned, v) or of(returned, contexted(v).value),
                raising(ReturningError("externally returned value")),
            )
            |then>> on(to(in_isolation), contextual)
            |then>> to_context(on(nothing, obj()))
            |then>> (lines[:-1] >= discretely((lambda line: lambda value: (
                result
                if of(returned, (result := line(value)).value)
                else value
            ))))
            |then>> (_get if len(lines) == 0 else lines[-1])
            |then>> saving_context(on(of(returned), attrgetter("value")))
            |then>> on(
                to(in_isolation),
                attrgetter("value"),
                else_=to_context(on(obj(), nothing)),
            )
        )


up: LeftCallable[
    Union[
        Callable[
            Callable[A, ContextualForm[C, B]],
            Callable[M, ContextualForm[F, Special[ContextualForm[G, V]]]]
        ],
        ActionChain[Callable[
            Callable[A, ContextualForm[C, B]],
            Callable[M, ContextualForm[F, Special[ContextualForm[V, G], W]]]
        ]],
    ],
    LeftCallable[
        Callable[A, ContextualForm[C, B]],
        LeftCallable[M, contextual[F | G, V | W]]
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
