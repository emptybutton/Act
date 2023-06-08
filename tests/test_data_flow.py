from typing import Any, Iterable

from pytest import mark

from pyhandling.data_flow import *
from pyhandling.testing import calling_test_case_of
from tests.mocks import Counter


test_eventually = calling_test_case_of(
    (lambda: eventually(lambda a, b: a + b, 100, 28)(1, 2, 3), 128),
    (lambda: eventually(lambda a, b: a + b, 100, 28)(), 128),
)


@mark.parametrize('call_number', tuple(range(4)) + (8, 128, 1024))
def test_returnly_call_number(call_number: int):
    call_counter = Counter()

    returnly_proxy_counter = returnly(call_counter)

    for _ in range(call_number):
        returnly_proxy_counter(2)

    assert call_counter.counted == call_number * 2


test_returnly = calling_test_case_of(
    (lambda: returnly(lambda _: _)(4), 4),
    (lambda: returnly(lambda _: ...)(4), 4),
    (lambda: returnly(lambda _: ...)(None), None),
    (lambda: returnly(lambda a, b, c: ...)(1, 2, 3), 1),
)


@mark.parametrize(
    "value, arguments",
    [
        (256, tuple()),
        (42, (1, 2, 3)),
        (None, (1, 2, 3)),
    ]
)
def test_to_action(value: Any, arguments: Iterable):
    assert to(value)(*arguments) == value


@mark.parametrize(
    'infix, result',
    [
        (to, 16), (by, 12)
    ]
)
def test_single_application_infix(infix: PartialApplicationInfix, result: Any):
    assert ((lambda a, b, c: (a + b) * c) |infix| 2)(2, 4) == result


@mark.parametrize(
    'infix, result',
    [
        (to, 39), (by, 64)
    ]
)
def test_keyword_application_infix(infix: PartialApplicationInfix, result: Any):
    assert ((lambda a, b, c: (a + b) * c) |infix* (5, 8))(3) == result
