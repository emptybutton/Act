from typing import runtime_checkable, Protocol

from pyhandling.annotations import AtomT


__all__ = ("Atomizable", "atomic")


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
