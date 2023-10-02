from typing import Self

from act.atomization import *
from act.pipeline import ActionChain
from act.testing import case_of


class AtomizableMock:
    def __init__(self, *, is_atom: bool = False):
        self.is_atom = is_atom

    def __eq__(self, other: Self) -> bool:
        return self.is_atom is other.is_atom

    def __getatom__(self) -> Self:
        return type(self)(is_atom=True)


test_atomic = case_of(
    (lambda: atomic(AtomizableMock()), AtomizableMock(is_atom=True))
)


test_fun = case_of(
    (lambda: isinstance(fun(ActionChain([int, str])), ActionChain), False),
    (
        lambda: len(ActionChain([fun(ActionChain([int, str])), print])),
        2
    ),
    (lambda: fun(lambda a: a)(4), 4),
)
