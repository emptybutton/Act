from abc import ABC, abstractmethod
from functools import partial
from inspect import isbuiltin, isfunction, ismethod
from operator import eq
from typing import Generic, Callable

from pyhandling.annotations import (
    V, dirty, reformer_of, checker_of, ActionT, action_for, Pm, R
)


__all__ = (
    "LeftCallable",
    "documenting_by",
    "to_check",
    "as_action",
    "action_repr_of",
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
    return determinant if callable(determinant) else partial(eq, determinant)


def as_action(value: ActionT | V) -> ActionT | action_for[V]:
    return value if callable(value) else lambda *_, **__: value


def action_repr_of(action: Callable) -> str:
    if ismethod(action):
        repr_ = f"({action_repr_of(action.__self__)}).{action.__name__}"
    elif isbuiltin(action):
        repr_ = action.__name__
    elif isfunction(action) or isinstance(action, type):
        repr_ = action.__qualname__
    else:
        return str(action)

    return repr_


def _module_prefix_of(action: Callable) -> str:
    prefix = str() if action.__module__ is None else action.__module__

    return str() if prefix in ("__main__", "builtins") else prefix + '.'

