from functools import partial
from dataclasses import dataclass
from typing import TypeVar, Callable, Generic, Optional, Self, Final, Any

from pyannotating import Special

from pyhandling.annotations import V, R, C, M, reformer_of
from pyhandling.branching import then
from pyhandling.contexting import contexted, contextual
from pyhandling.data_flow import by, yes
from pyhandling.immutability import property_to
from pyhandling.operators import not_
from pyhandling.synonyms import on, returned
from pyhandling.tools import documenting_by, action_repr_of


__all__ = (
    "Access",
    "Effect",
    "as_effect",
    "context_effect",
)


_GetterT = TypeVar("_GetterT", bound=Callable)
_SetterT = TypeVar("_SetterT", bound=Callable)


@dataclass(frozen=True)
class Access(Generic[_GetterT, _SetterT]):
    """Aggregate class of getter and setter functions."""

    get: _GetterT
    set: _SetterT


_NO_EFFECT_VALUE: Final[object] = object()


class Effect(Generic[V, R, C]):
    """
    Aggregating decorator class for executing in a specific container type and
    actions for casting value to this container type.

    Aggregates an action of specifying a value as a container type (`is_lifted`),
    casting it to a container type (`lift`), and representing it to a container
    type (`lifted`).

    Decorates like an input decorator, with the exception that when a decorated
    action is calling with a value not cast to a container type, represents them
    to a container type. The result is also presented to a container type.

    Has the ability to additionally decorate an input decorator while preserving
    actions of casting to a container type.

    Partially applicable to keyword arguments, i.e. when passing only keyword
    arguments, it is equivalent to `partial(Effect, **keywords)`.
    """

    lift = property_to("lift")
    is_lifted = property_to("is_lifted")

    def __new__(
        cls,
        decorator: Optional[Callable[
            Callable[V, R | C],
            Callable[C, C | M],
        ]] = None,
        /,
        **kwargs,
    ) -> Self | Callable[Callable[Callable[V, R | C], Callable[C, C | M]], Self]:
        return (
            partial(Effect, **kwargs)
            if decorator is None
            else super().__new__(cls)
        )

    def __init__(
        self,
        decorator: Callable[Callable[V, R], Callable[C, C | M]],
        /,
        *,
        lift: Callable[V | M, C],
        is_lifted: Callable[V | M | C, bool],
    ):
        self._decorator = decorator
        self._lift = lift
        self._is_lifted = is_lifted

    def __repr__(self) -> str:
        return f"Effect({action_repr_of(self._decorator)})"

    def __call__(
        self,
        action: Callable[V, R | C],
        value: Special[V | C] = _NO_EFFECT_VALUE,
    ) -> Callable[V | C, C] | C:
        lifted_action = self.lifted |then>> self._decorator(action) >> self.lifted

        return (
            lifted_action
            if value is _NO_EFFECT_VALUE
            else lifted_action(value)
        )

    def lifted(self, value: V | M | C, /) -> C:
        """Method to represent an input value to a container type."""

        return value if self._is_lifted(value) else self._lift(value)

    def by(
        self,
        metadecorator: reformer_of[Callable[
            Callable[V, R | C],
            Callable[C, C | M],
        ]],
        /,
    ) -> Self:
        return type(self)(
            metadecorator(self._decorator),
            lift=self._lift,
            is_lifted=self._is_lifted,
        )


as_effect: Callable[
    Effect[V, R, C] | Callable[Callable[V, R], Callable[C, C]],
    Effect[V, R, C],
]
as_effect = documenting_by(
    """
    Function representing an input decorator in `Effect` form.
    When an input decorator is already in the `Effect` form returns the form.
    """
)(
    on(not_(isinstance |by| Effect), Effect(lift=returned, is_lifted=yes))
)


context_effect: Callable[
    Callable[Callable[V, R], Callable[C, C]],
    Effect[V, R, contextual[C, Any]],
]
context_effect = documenting_by(
    """`Effect` constructor with container type as `contextual`."""
)(
    Effect(lift=contexted, is_lifted=isinstance |by| contextual)
)
