from typing import Callable, Any

from pyhandling.annotations import action_of, notes_of, pure, dirty
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import with_attributes


test_action_of = calling_test_case_of(
    (lambda: action_of[tuple()], Callable),
    (lambda: action_of[int], Callable[[int], Any]),
    (lambda: action_of[int, float], Callable[[int], float]),
    (lambda: action_of[int, float, str], Callable[[int], Callable[[float], str]]),
    (
        lambda: action_of[int, float, str, set],
        Callable[[int], Callable[[float], Callable[[str], set]]]
    ),
    (
        lambda: action_of[None, None, None],
        Callable[[None], Callable[[None], None]]
    ),
    (
        lambda: action_of['ann', 'ann', 'ann'],
        Callable[['ann'], Callable[['ann'], 'ann']],
    ),
)


test_noting = calling_test_case_of(
    (lambda: notes_of(None), tuple()),
    (lambda: notes_of(list()), tuple()),
    (lambda: notes_of(pure(dirty(with_attributes()))), (dirty, pure)),
)