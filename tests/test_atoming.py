from typing import Self

from pyhandling.atoming import *
from pyhandling.branching import ActionChain
from pyhandling.testing import calling_test_case_of


class AtomizableMock:
    def __init__(self, *, is_atom: bool = False):
        self.is_atom = is_atom

    def __eq__(self, other: Self) -> bool:
        return self.is_atom is other.is_atom

    def __getatom__(self) -> Self:
        return type(self)(is_atom=True)


test_atomic = calling_test_case_of(
    (lambda: atomic(AtomizableMock()), AtomizableMock(is_atom=True))
)


test_atomically = calling_test_case_of(
    (lambda: isinstance(atomically(ActionChain([int, str])), ActionChain), False),
    (
        lambda: len(ActionChain([atomically(ActionChain([int, str])), print])),
        2
    ),
    (lambda: atomically(lambda a: a)(4), 4),
)
