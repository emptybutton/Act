from abc import ABC
from operator import not_, methodcaller, attrgetter
from typing import (
    Generic, Any, Iterator, Callable, Iterable, GenericAlias, Self, TypeVar,
    Final, Union
)

from pyannotating import Special

from act.annotations import (
    ActionT, ErrorT, P, Pm, A, B, C, V, R, W, D, S, M, G, F, Unia, FlagT
)
from act.atomization import atomically
from act.flags import (
    nothing, Flag, pointed, flag_about, _NamedFlag, _CallableNamedFlag
)
from act.immutability import NotInitializable
from act.partiality import partially, will, rpartial
from act.pipeline import then, ActionChain, discretely, atomic_binding_by
from act.representations import code_like_repr_of
from act.signatures import call_signature_of
from act.synonyms import repeating, returned, on
from act.tools import documenting_by, LeftCallable


__all__ = (
    "contextual_like",
    "ContextualForm",
    "contextual",
    "contextually",
    "ContextualError",
    "context_oriented",
    "contexted",
    "contextualizing",
    "as_",
    "saving_context",
    "to_context",
    "to_write",
    "to_read",
    "with_context_that",
    "to_metacontextual",
    "is_metacontextual",
    "with_reduced_metacontext",
    "without_metacontext",
    "up",
)


class contextual_like(NotInitializable):
    """
    Annotation class of objects that can be cast to `ContextualForm`.

    Such objects are iterable objects consisting a main value as first item and
    a context describing the main value as second item.

    Checks using the `isinstance` function.

    The `[]` callback can be used to create an appropriate annotation with a
    description of values in the corresponding places.

    When passing an annotation of only a main value, a context will be of `Any`
    type.
    """

    def __class_getitem__(
        cls,
        value_or_value_and_context: Any | tuple[Any, Any],
    ) -> GenericAlias:
        value_and_context = (
            value_or_value_and_context
            if isinstance(value_or_value_and_context, Iterable)
            else (value_or_value_and_context, Any)
        )

        value, context = value_and_context

        return tuple[value, context]

    @classmethod
    def __instancecheck__(cls, instance: Any) -> bool:
        return isinstance(instance, Iterable) and len(tuple(instance)) == 2

    @classmethod
    def __subclasscheck__(cls, type_: type) -> bool:
        return issubclass(type_, Iterable)


class ContextualForm(ABC, Generic[V, C]):
    """
    Abstract value form class for holding an additional value, describing the
    main value.

    Comparable by form implementation and stored values.

    Iterable over stored values for unpacking capability, where the first value
    is the main value and the second is the context describing the main value.

    Attributes for stored values are defined in concrete forms.
    """

    _value: V
    _context: C

    def __repr__(self) -> str:
        return "{} {}".format(
            self._context_repr_of(self._context),
            code_like_repr_of(self._value),
        )

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False

        value, context = other

        return self._value == value and self._context == context

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))

    def _context_repr_of(self, value: Special["contextual"]) -> str:
        return (
            f"({code_like_repr_of(value)})"
            if type(value) is contextual
            else code_like_repr_of(value)
        )


class _BinaryContextualForm(ContextualForm, Generic[V, C]):
    """`ContextualForm` class with nested creation."""

    def __init__(self, value: V | Self, *contexts: C):
        if len(contexts) > 1:
            value = type(self)(value, *contexts[:-1])

        self._reset(value, nothing if len(contexts) == 0 else contexts[-1])

    def _reset(self, value: V, context: C) -> None:
        self._value = value
        self._context = context


class contextual(_BinaryContextualForm, Generic[V, C]):
    """Basic `ContextualForm` form representing values with no additional effect."""

    value = property(attrgetter("_value"))
    context = property(attrgetter("_context"))


class contextually(LeftCallable, _BinaryContextualForm, Generic[ActionT, C]):
    """`ContextualForm` form for annotating actions with saving their call."""

    action = property(attrgetter("_value"))
    context = property(attrgetter("_context"))

    def __init__(self, action: Callable[Pm, R], *contexts: C):
        super().__init__(action, *contexts)
        self.__signature__ = call_signature_of(self._value)

    def __repr__(self) -> str:
        return f"contextually({super().__repr__()})"

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._value(*args, **kwargs)


class ContextualError(_BinaryContextualForm, Exception, Generic[ErrorT, C]):
    """
    `ContextualForm` form for annotating an error with a context while retaining
    the ability to `raise` the call.
    """

    error = property(attrgetter("_value"))
    context = property(attrgetter("_context"))

    def __init__(self, error: ErrorT, *contexts: C):
        super().__init__(error, *contexts)
        Exception.__init__(self, repr(self))

    def __repr__(self) -> str:
        return f"ContextualError({super().__repr__()})"

    def __str__(self) -> str:
        return repr(self)


def context_oriented(root_values: contextual_like[V, C]) -> contextual[C, V]:
    """
    Function to replace the main value of a `contextual_like` object with its
    context, and its context with its main value.
    """

    return contextual(*reversed(tuple(root_values)))


_NO_VALUE: Final[Flag] = flag_about("_NO_VALUE")


def contexted(
    value: V | ContextualForm[V, D],
    when: C | Callable[D, C] | _NO_VALUE = _NO_VALUE,
) -> ContextualForm[V, D | C]:
    """
    Function to represent an input value in `contextual` form if it is not
    already present.

    Forces a context, when passed, as the result of caaling the forced context
    if it is a callable, or as the forced context itself if not a callable.
    """

    value, context = (
        value if isinstance(value, ContextualForm) else contextual(value)
    )

    if callable(when) and not isinstance(when, Flag):
        context = when(context)
    elif when is not _NO_VALUE:
        context = when

    return contextual(value, context)


_NamedFlagT = TypeVar("_NamedFlagT", bound=_NamedFlag)


@partially
def contextualizing(
    flag: _NamedFlagT,
    *,
    to: Callable[[V, _CallableNamedFlag[V, R]], R] = contextual,
) -> _CallableNamedFlag[V, R]:
    """
    Function to add to a flag the ability to contextualize values with this flag.
    """

    contextualizing_flag = flag.to(lambda value: to(value, contextualizing_flag))

    return contextualizing_flag


@partially
def as_(
    flag: Unia[FlagT, Callable[V, ContextualForm[V, FlagT]]],
    value: V | ContextualForm[V, Special[FlagT, C]],
) -> ContextualForm[V, FlagT]:
    """Function to represent an input value contextualized by an input flag."""

    return value if contexted(value).context == flag else flag(value)


@partially
def saving_context(
    action: Callable[A, B],
    value_and_context: contextual_like[A, C] | A,
) -> contextual[B, C]:
    """
    Function to perform an input action on a `contextual_like` value while
    saving its context.
    """

    value, context = contexted(value_and_context)

    return contextual(action(value), context)


@partially
def to_context(
    action: Callable[A, B],
    value_and_context: contextual_like[V, A],
) -> contextual[V, B]:
    """
    Function to perform an input action on a context of `contextual_like` value
    while saving its value.
    """

    return context_oriented(saving_context(
        action,
        context_oriented(contexted(value_and_context)),
    ))


@partially
def to_write(
    action: Callable[[V, C], R],
    value: contextual_like[V, C],
) -> contextual[V, R]:
    """
    Function to perform an input action on a `contextual_like` context, with
    passing its main value.
    """

    stored_value, context = value

    return contextual(stored_value, action(stored_value, context))


@partially
def to_read(
    action: Callable[[V, C], R],
    value: contextual_like[V, C],
) -> contextual[R, V]:
    """
    Function to perform an input action on a `contextual_like` main value, with
    passing its context.
    """

    return context_oriented(to_write(action, context_oriented(value)))


@partially
def with_context_that(
    that: Callable[P, bool],
    value: V | ContextualForm[V, P | Flag[P]],
) -> contextual[V, P | nothing]:
    """
    Function for transform `ContextualForm` with context filtered by input
    checker.

    When a context is `Flag`, the resulting context will be filtered by any of
    its values.

    Returns `nothing` if a context is invalid for an input checker`.
    """

    return to_context(
        pointed |then>> (methodcaller("that", that) |then>> attrgetter("point"))
    )(value)


def to_metacontextual(
    value_action: Callable[V, W] = returned,
    context_action: Callable[C, D] = returned,
    /,
    *,
    summed: Callable[contextual[W, D] | S, S] = returned,
) -> LeftCallable[contextual_like[V, C] | V, S]:
    """
    Reduce function for values of nested `ContextualForms`.

    Calculates from `value_action` and `context_action` corresponding leaf
    values.

    Calculates a form with calculated values by `summed`.
    """

    value_action, context_action = tuple(map(
        will(on)(
            rpartial(isinstance, ContextualForm) |then>> not_,
            else_=lambda v: to_metacontextual(
                value_action,
                context_action,
                summed=summed,
            )(v),
        ),
        (value_action, context_action),
    ))

    return atomically(
        contexted
        |then>> saving_context(value_action)
        |then>> to_context(context_action)
        |then>> summed
    )


def is_metacontextual(
    value: Special[ContextualForm[ContextualForm, Any], Any],
) -> bool:
    """
    Function to check `ContextualForm`s describing another `ContextualForm` if
    it is at all `ContextualForm`.
    """

    return (
        isinstance(value, ContextualForm)
        and isinstance(value.value, ContextualForm)
    )


def with_reduced_metacontext(
    value: ContextualForm[ContextualForm[V, Any], Any]
) -> contextual[V, Flag]:
    """
    Function to remove nesting of two `ContextualForm`s.
    The resulting context is a flag sum from the top and bottom `ContextualForm`.
    """

    meta_root = contextual(*value)
    root = meta_root.value

    return contexted(root, +pointed(meta_root.context))


without_metacontext: LeftCallable[ContextualForm, contextual]
without_metacontext = documenting_by(
    """
    Function to fully glue nested `ContextualForm`s.
    The resulting context is a flag sum from all nested `ContextualForm`s.
    """
)(
    repeating(with_reduced_metacontext, while_=is_metacontextual)
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
up = discretely(atomic_binding_by(
    ...
    |then>> atomic_binding_by(... |then>> with_reduced_metacontext)
))
