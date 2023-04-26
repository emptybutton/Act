from functools import update_wrapper
from typing import runtime_checkable, Protocol, Self

from pyhandling.annotations import AtomizableT, action_for, R
from pyhandling.errors import AtomizationError


__all__ = ("Atomizable", "atomic", "atomically")


@runtime_checkable
class Atomizable(Protocol):
    """
    Protocol for objects capable of being converted to atomic form.

    The `atomic` function is used to convert.
    """

    def __getatom__(self) -> Self:
        ...


def atomic(value: AtomizableT) -> AtomizableT:
    """
    Function representing an input object in its atomic form.

    Is a public synonym for calling the `__getatom__` method.
    """

    if not isinstance(value, Atomizable):
        raise AtomizationError(f"{type(value).__name__} object is not atomizable'")

    return value.__getatom__()


class atomically:
    """
    Decorator that removes the behavior of an input action, leaving only
    calling.
    """

    def __init__(self, action: action_for[R]):
        self._action = action
        update_wrapper(self, self._action)

    def __repr__(self) -> str:
        return f"atomically({self._action})"

    def __call__(self, *args, **kwargs) -> R:
        return self._action(*args, **kwargs)
