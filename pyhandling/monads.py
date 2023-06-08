from operator import attrgetter, call, eq
from typing import Callable, Any, Tuple, Optional

from pyannotating import Special

from pyhandling.aggregates import context_effect
from pyhandling.annotations import (
    dirty, R, checker_of, event_for, A, B, V, FlagT, C, ActionT
)
from pyhandling.atoming import atomically
from pyhandling.branching import (
    discretely, ActionChain, binding_by, matching, then
)
from pyhandling.contexting import (
    contextual, contextually, contexted, ContextRoot, saving_context, to_write,
    to_read, to_context, with_reduced_metacontext
)
from pyhandling.data_flow import returnly, by, to
from pyhandling.flags import flag_about, nothing, Flag, pointed
from pyhandling.objects import namespace_of
from pyhandling.objects import void
from pyhandling.operators import and_, not_
from pyhandling.partials import will, partially
from pyhandling.structure_management import tmap
from pyhandling.synonyms import on
from pyhandling.tools import documenting_by, to_check, as_action, LeftCallable


__all__ = (
    "ok",
    "bad",
    "maybe",
    "until_error",
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


ok = flag_about('ok')
bad = flag_about('bad', negative=True)


@documenting_by(
    """
    Effect to stop an execution when an input value is None or returned in the
    `bad` context.

    Atomically applied to actions in `ActionChain`.
    """
)
@context_effect
@discretely
@will
def maybe(
    action: Callable[A, B],
    value: contextual[Optional[A], Special[bad, FlagT]],
) -> contextual[Optional[A | B], Special[bad, FlagT]]:
    stored_value, context = value

    if contexted(stored_value).context == bad:
        return contexted(stored_value, +pointed(context))
    elif stored_value is None or context == bad:
        return value
    else:
        return value >= (
            saving_context(action)
            |then>> on(
                lambda result: contexted(result).context == bad,
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
    action: Callable[[A], B],
    value: ContextRoot[A, Special[Exception | Flag[Exception] | C]],
) -> contextual[A | B, Flag[Exception] | C]:
    if pointed(value.context).that(isinstance |by| Exception) != nothing:
        return value

    try:
        return saving_context(action, value)
    except Exception as error:
        return contexted(value, +pointed(error))


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


right = flag_about("right")
left = flag_about("left", negative=True)


def either(
    *determinants_and_ways: tuple[
        Special[checker_of[C]],
        Callable[[contextual[V, C]], R] | R,
    ],
) -> LeftCallable[V | contextual[V, C], R]:
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
            saving_context(as_action(way)),
        )
        for determinant, way in determinants_and_ways
    )))


future = flag_about("future")


@partially
def in_future(
    action: Callable[[V], R],
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

    return contexted(value, +pointed(contextually(action |to| value, when=future)))


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


is_in_future: Callable[Special[contextually[Callable, Special[future]]], bool]
is_in_future = documenting_by(
    """Function to check if an input value is a `in_future` deferred action."""
)(
    and_(
        isinstance |by| contextually,
        attrgetter("context") |then>> (eq |by| future),
    )
)


@namespace_of
class do:
    writing = flag_about("writing")
    reading = flag_about("reading")

    returned = flag_about("returned")

    def write(action: ActionT) -> contextually[ActionT, writing]:
        return contextually(action, do.writing)

    def read(action: ActionT) -> contextually[ActionT, reading]:
        return contextually(action, do.reading)

    def return_(value: V) -> contextual[V, returned]:
        return contextual(value, do.returned)

    def __call__(*actions: ActionT) -> LeftCallable[Any, contextual]:
        lines = ((map |by| actions) |then>> ActionChain)(
            discretely(
                either(
                    (do.writing, to_write),
                    (do.reading, to_read),
                    (..., saving_context),
                )
                |then>> attrgetter("value")
                |then>> will(on)(not_(do._is_for_returning))
            )
            |then>> atomically
        )

        lines = (
            (lines[:-1] >= discretely(will(lambda action, root: (
                contextual(root.value, action(root).context)
            ))))
            |then>> lines
        )
        
        return atomically(
            contexted
            |then>> to_context(on(nothing, void))
            |then>> (lines[:-1] >= discretely(will(lambda action, root: (
                contextual(root.value, action(root).context)
            ))))
            |then>> lines[-1]
            |then>> to_context(on(void, nothing))
        )

    _is_for_returning = (lambda root: contexted(root.value).context == do.returned)


# (lines[:-1] >= discretely(lambda action: on(
#     not_(do._is_for_returning),
#     lambda root: contextual(root.value, action(root.value).context),
# )))

# contextual(root.value, action(root).context)))
# on(
#     lambda r: contexted(r.value).context != do.returned,
#     attrgetter("context") |then>> (contextual |to| root.value),
# )

# print(type(lines[:-1]).__name__)

# action(root) >= on(
#     lambda r: contexted(r.value).context != do.returned,
#     attrgetter("context") |then>> (contextual |to| root.value),
# )

# @namespace_of
# class do:
#     writing = flag_about("writing")
#     reading = flag_about("reading")
#     flags = writing | reading

#     def write(action: ActionT) -> contextually[ActionT, writing]:
#         return contextually(action, writing)

#     def read(action: ActionT) -> contextually[ActionT, reading]:
#         return contextually(action, reading)

#     def __call__(
#         *lines: Callable[A, B],
#     ) -> LeftCallable[A | ContextRoot[A, Any], contextual[B, Any]]:
#         return do._run(do._lines_of(lines))

#     def _lines_of(
#         actions: Iterable[Callable[A, B]]
#     ) -> ActionChain[Callable[ContextRoot[A, Any], contextual[B, Any]]]:
#         return ((map |by| actions) |then>> ActionChain)(discretely(
#             either(
#                 (do.writing, to_write),
#                 (do.reading, to_read),
#                 (..., saving_context),
#             )
#             |then>> attrgetter("value")
#         ))

#     @partially
#     def _run(
#         lines: ActionChain[Callable[ContextRoot[A, Any], contextual[B, C]]],
#         value: A | ContextRoot[A, Any],
#     ) -> contextual[B, C]:
#         root = contexted(value)

#         for line in lines[:-1]:
#             root = contextual(root.value, line(root).context)

#         return atomically(
#             contexted
#             |then>> to_context(on(nothing, void))
#             |then>> (lines[:-1] >= discretely(will(lambda action, root: (
#                 contextual(root.value, action(root).context)
#             ))))
#             |then>> lines[-1]
#             |then>> to_context(on(void, nothing))
#         )
