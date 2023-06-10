from operator import truediv, add, sub
from typing import Any, Iterable

from pytest import mark, raises

from pyhandling.data_flow import *
from pyhandling.testing import case_of
from tests.mocks import Counter


test_eventually = case_of(
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


test_returnly = case_of(
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


test_with_result = case_of(
    (lambda: with_result(8, lambda a, b, c: 42)(1, 2, 3), 8),
)


test_to_left = case_of(
    (lambda: to_left(lambda v: v + 3)(5, ...), 8),
)


test_to_right = case_of(
    (lambda: to_right(lambda v: v + 3)(..., 5), 8),
)


test_dynamically = case_of(
    (lambda: dynamically(truediv, add, sub)(5, 3), 4),
)


test_double = case_of(
    (lambda: double(lambda a: lambda b, c, d=0: a/b + c/d)(10, 2, 6, d=2), 8),
)


def test_once():
    def raise_zero_division_error():
        raise ZeroDivisionError()

    action = once(raise_zero_division_error)

    with raises(ZeroDivisionError):
        assert action() is None

    assert action() is None


test_via_items = case_of(
    (lambda: via_items(lambda v: v + 3)[5], 8),
    (lambda: via_items(truediv)[8, 2], 4),
)


test_yes = case_of(
    (lambda: yes(1, 2, 3), True),
    (lambda: yes(), True),
)


test_no = case_of(
    (lambda: no(1, 2, 3), False),
    (lambda: no(), False),
)


test_anything = case_of(
    (lambda: anything == anything),
    (lambda: anything == 4),
    (lambda: anything is None),
)
