from abc import ABC
from operator import not_, methodcaller, attrgetter
from typing import (
    Generic, Any, Iterator, Callable, Iterable, GenericAlias, TypeVar,
    Final
)

from pyannotating import Special

from act.annotations import (
    ActionT, ErrorT, P, Pm, A, B, C, V, R, W, D, S, Unia, FlagT
)
from act.atomization import func
from act.data_flow import and_via_indexer
from act.flags import (
    nothing, Flag, pointed, flag_about, FlagVector, _NamedFlag, _CallableNamedFlag
)
from act.immutability import NotInitializable
from act.partiality import partially, will, rpartial
from act.pipeline import then
from act.representations import code_like_repr_of
from act.signatures import call_signature_of
from act.synonyms import while_, on
from act.tools import documenting_by, LeftCallable, _get


__all__ = (
    "contextual_like",
    "ContextualForm",
    "contextual",
    "contextually",
    "ContextualError",
    "context_oriented",
    "contexted",
    "contextualizing",
    "be",
    "of",
    "saving_context",
    "to_context",
    "to_write",
    "to_read",
    "with_context_that",
    "to_metacontextual",
    "is_metacontextual",
    "with_reduced_metacontext",
    "without_metacontext",
    "metacontexted",
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
        value_or_context_and_value: Any | tuple[Any, Any],
    ) -> GenericAlias:
        context_and_value = (
            value_or_context_and_value
            if isinstance(value_or_context_and_value, Iterable)
            else (Any, value_or_context_and_value)
        )

        context, value = context_and_value

        return tuple[context, value]

    @classmethod
    def __instancecheck__(cls, instance: Any) -> bool:
        return isinstance(instance, Iterable) and len(tuple(instance)) == 2

    @classmethod
    def __subclasscheck__(cls, type_: type) -> bool:
        return issubclass(type_, Iterable)


class ContextualForm(ABC, Generic[C, V]):
    """
    Abstract value form class for holding an additional value, describing the
    main value.

    Comparable by form implementation and stored values.

    Iterable over stored values for unpacking capability, where the first value
    is the main value and the second is the context describing the main value.

    Attributes for stored values are defined in concrete forms.
    """

    def __init__(self, arg: V | C, *args: V | C):
        args = (arg, *args)

        if len(args) == 1:
            self._set(nothing, args[0])
        elif len(args) == 2:
            self._set(args[0], args[1])
        else:
            self._set(args[0], type(self)(*args[1:]))

    def _set(self, context: C, value: V) -> None:
        self._context = context
        self._value = value

    def __repr__(self) -> str:
        return "{} {}".format(
            self._context_repr_of(self._context),
            code_like_repr_of(self._value),
        )

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False

        context, value = other

        return self._value == value and self._context == context

    def __iter__(self) -> Iterator:
        return iter((self._context, self._value))

    def __class_getitem__(cls, annotations: Special[tuple]) -> GenericAlias:
        if not isinstance(annotations, tuple):
            return cls[nothing, annotations]
        elif len(annotations) == 2:
            return super().__class_getitem__(annotations)
        else:
            return super().__class_getitem__((annotations[0], cls[annotations[1:]]))

    def _context_repr_of(self, value: Special["contextual"]) -> str:
        return (
            f"({code_like_repr_of(value)})"
            if type(value) is contextual
            else code_like_repr_of(value)
        )


class contextual(ContextualForm, Generic[C, V]):
    """Basic `ContextualForm` form representing values with no additional effect."""

    value = property(attrgetter("_value"))
    context = property(attrgetter("_context"))


class contextually(LeftCallable, ContextualForm, Generic[C, ActionT]):
    """`ContextualForm` form for annotating actions with saving their call."""

    action = property(attrgetter("_value"))
    context = property(attrgetter("_context"))

    def _update(self, context: C, value: Callable[Pm, R]) -> None:
        super()._update(context, value)
        self.__signature__ = call_signature_of(self._value)

    def __repr__(self) -> str:
        return f"callable({super().__repr__()})"

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._value(*args, **kwargs)


class ContextualError(ContextualForm, Exception, Generic[ErrorT, C]):
    """
    `ContextualForm` form for annotating an error with a context while retaining
    the ability to `raise` the call.
    """

    error = property(attrgetter("_value"))
    context = property(attrgetter("_context"))

    def _update(context: C, value: ErrorT) -> None:
        super()._update(context, value)

    def __repr__(self) -> str:
        return f"raisable({super().__repr__()})"

    def __str__(self) -> str:
        return repr(self)


def context_oriented(value: Special[ContextualForm[C, V]]) -> contextual[V, C]:
    """
    Function to replace the main value of a `ContextualForm` with its context,
    and its context with its main value.
    """

    return (
        contextual(*reversed(tuple(value)))
        if isinstance(value, ContextualForm)
        else contextual(value, nothing)
    )


_NO_VALUE: Final[Flag] = flag_about("_NO_VALUE")


@and_via_indexer(lambda a, b=_NO_VALUE: (
    contexted[Any, a]
    if b is _NO_VALUE
    else b | ContextualForm[a, b]
))
def contexted(
    value: V | ContextualForm[D, V],
    when: C | Callable[D, C] | _NO_VALUE = _NO_VALUE,
) -> contextual[D | C, V]:
    """
    Function to represent an input value in `contextual` form if it is not
    already present.

    Forces a context, when passed, as the result of caaling the forced context
    if it is a callable, or as the forced context itself if not a callable.
    """

    context, value = (
        value if isinstance(value, ContextualForm) else contextual(value)
    )

    if callable(when) and not isinstance(when, Flag):
        context = when(context)
    elif when is not _NO_VALUE:
        context = when

    return contextual(context, value)


_NamedFlagT = TypeVar("_NamedFlagT", bound=_NamedFlag)


@partially
def contextualizing(
    flag: _NamedFlagT,
    *,
    to: Callable[[_CallableNamedFlag[V, R], V], R] = contextual,
) -> _CallableNamedFlag[V, R]:
    """
    Function to add to a flag the ability to contextualize values with this flag.
    """

    contextualizing_flag = flag.to(lambda value: to(contextualizing_flag, value))

    return contextualizing_flag


@partially
def be(
    flag_or_vector: FlagT | Unia[FlagT, Callable[V, ContextualForm[FlagT, V]]] | FlagVector,
    value: V | ContextualForm[Special[FlagT, C], V],
) -> ContextualForm[Special[FlagT], V]:
    """
    Function to represent an input value contextualized by an input flag.

    Represents in contextual form using an input `FlagVector` when it passed
    as a flag.
    """

    if isinstance(flag_or_vector, FlagVector):
        return contexted(value, flag_or_vector)
    elif contexted(value).context == flag_or_vector:
        return value
    elif callable(flag_or_vector):
        return flag_or_vector(value)
    else:
        return contextual(flag_or_vector, value)


@partially
def of(context: C, value: Special[ContextualForm[C, Any]]) -> bool:
    """Shortcut to compare input value with context of second input value."""

    return contexted(value).context == context


@partially
def saving_context(
    action: Callable[A, B],
    value: ContextualForm[C, A] | A,
) -> contextual[C, B]:
    """
    Function to perform an input action to a `ContextualForm` value while
    saving its context.
    """

    context, stored_value = contexted(value)

    return contextual(context, action(stored_value))


@partially
def to_context(
    action: Callable[A | nothing, B],
    value: contextual_like[A, V] | V,
) -> contextual[B, V]:
    """
    Function to perform an input action on a context of `contextual_like` value
    while saving its value.
    """

    return context_oriented(saving_context(action, context_oriented(value)))


@partially
def to_write(
    action: Callable[[C, V], R],
    value: contextual_like[C, V],
) -> contextual[R, V]:
    """
    Function to perform an input action on a `contextual_like` context, with
    passing its main value.
    """

    context, stored_value = value

    return contextual(action(context, stored_value), stored_value)


@partially
def to_read(
    action: Callable[[C, V], R],
    value: contextual_like[C, V],
) -> contextual[V, R]:
    """
    Function to perform an input action on a `contextual_like` main value, with
    passing its context.
    """

    context, stored_value = value

    return contextual(context, action(context, stored_value))


@partially
def with_context_that(
    that: Callable[P, bool],
    value: V | ContextualForm[P | Flag[P], V],
) -> contextual[P | nothing, V]:
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
    context_action: Callable[C, D],
    value_action: Callable[V, W],
    /,
    *,
    summed: Callable[contextual[D, W] | S, S] = _get,
) -> LeftCallable[contextual_like[C, V] | V, S]:
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
                context_action,
                value_action,
                summed=summed,
            )(v),
        ),
        (value_action, context_action),
    ))

    return func(
        contexted
        |then>> saving_context(value_action)
        |then>> to_context(context_action)
        |then>> summed
    )


def is_metacontextual(value: Special[ContextualForm[Any, Any, Any]]) -> bool:
    """
    Function to check `ContextualForm`s describing another `ContextualForm` if
    it is at all `ContextualForm`.
    """

    return (
        isinstance(value, ContextualForm)
        and isinstance(value.value, ContextualForm)
    )


def with_reduced_metacontext(
    value: ContextualForm[Any, Any, V] | ContextualForm[C, V] | V
) -> contextual[C | Flag, V]:
    """
    Function to remove nesting of two `ContextualForm`s.
    The resulting context is a flag sum from the top and bottom `ContextualForm`.
    """

    context, value = contexted(value)

    return (
        contextual(
            pointed(context, contexted(value).context),
            contexted(value).value,
        )
        if isinstance(value, ContextualForm)
        else contextual(context, value)
    )


without_metacontext: LeftCallable[ContextualForm, contextual]
without_metacontext = documenting_by(
    """
    Function to fully glue nested `ContextualForm`s.
    The resulting context is a flag sum from all nested `ContextualForm`s.
    """
)(
    while_(is_metacontextual, with_reduced_metacontext)
)


def metacontexted(value: Special[ContextualForm]) -> tuple:
    """Function to get a value and all its contexts as a flat collection."""

    if not isinstance(value, ContextualForm):
        return (value, )

    value = contextual(*value)

    return (value.context, *metacontexted(value.value))
