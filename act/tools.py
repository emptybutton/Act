from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from operator import eq
from typing import Generic, Callable, Any, Tuple, Mapping, Optional

from pyannotating import Special

from act.annotations import (
    V, dirty, reformer_of, checker_of, ActionT, action_for, Pm, R, K
)


__all__ = (
    "LeftCallable",
    "documenting_by",
    "to_check",
    "as_action",
    "time_of",
    "items_of",
    "maybe_getattr",
    "maybe_getitem",
)


class LeftCallable(ABC, Generic[Pm, R]):
    """
    Mixin class to add a one value call synonyms `>=` and `<=` where is it on
    the right i.e. `value >= instance` and less preferred `instance <= value`.
    """

    @abstractmethod
    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        ...

    def __le__(self, value: Pm) -> R:
        return self(value)


def documenting_by(documentation: str) -> dirty[reformer_of[V]]:
    """
    Function of getting other function that getting value with the input
    documentation from this first function.
    """

    def document(object_: V) -> V:
        """
        Function created with `documenting_by` function that sets the __doc__
        attribute and returns the input object.
        """

        object_.__doc__ = documentation
        return object_

    return document


def to_check(determinant: checker_of[V] | V) -> checker_of[V]:
    """Function representing an input value to a validation action."""

    from act.flags import _CallableNamedFlag
    from act.partiality import partial

    return (
        determinant
        if callable(determinant) and not isinstance(determinant, _CallableNamedFlag)
        else partial(eq, determinant)
    )


def as_action(value: ActionT | V) -> ActionT | action_for[V]:
    """Function representing an input value to aт action."""

    return value if callable(value) else lambda *_, **__: value


def time_of(action: Callable[[], Any]) -> timedelta:
    """Function to get run time measurement of an input action."""

    start = datetime.now()
    action()

    return datetime.now() - start


def items_of(items: V | Tuple[V]) -> Tuple[V]:
    """Function for structured getting inside indexer (`[]`)."""

    return items if isinstance(items, tuple) else (items, )


def maybe_getattr(object_: Any, attr_name: str) -> Special[None]:
    return getattr(object_, attr_name) if hasattr(object_, attr_name) else None


def maybe_getitem(table: Mapping[K, V], key: Special[K]) -> Optional[V]:
    return table[key] if key in tuple(table.keys()) else None


def _module_prefix_of(action: Callable) -> str:
    prefix = str() if action.__module__ is None else action.__module__

    return str() if prefix in ("__main__", "builtins") else prefix + '.'
