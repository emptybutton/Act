from functools import update_wrapper
from typing import runtime_checkable, Protocol

from pyhandling.annotations import AtomT, action_for, ResultT


__all__ = ("Atomizable", "atomic", "atomically")


@runtime_checkable
class Atomizable(Protocol[AtomT]):
    """
    Protocol for objects capable of being converted to atomic form.

    The `atomic` function is used to convert.
    """

    def __getatom__(self) -> AtomT:
        ...


def atomic(value: Atomizable[AtomT]) -> AtomT:
    """
    Function representing an input object in its atomic form.

    Is a public synonym for calling the `__getatom__` method.
    """

    return value.__getatom__()


class atomically:
    """
    Decorator that removes the behavior of an input action, leaving only
    calling.
    """

    def __init__(self, action: action_for[ResultT]):
        self._action = action
        update_wrapper(self, self._action)

    def __repr__(self) -> str:
        return f"atomically({self._action})"

    def __call__(self, *args, **kwargs) -> ResultT:
        return self._action(*args, **kwargs)
