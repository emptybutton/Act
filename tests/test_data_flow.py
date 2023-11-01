from operator import truediv, add, sub
from typing import Any, Iterable

from pytest import mark, raises

from act.data_flow import *
from act.testing import case_of


test_always = case_of(
    (lambda: always(lambda a, b: a + b, 100, 28)(1, 2, 3), 128),
    (lambda: always(lambda a, b: a + b, 100, 28)(), 128),
)


test_io = case_of(
    (lambda: io(lambda _: _)(4), 4),
    (lambda: io(lambda _: ...)(4), 4),
    (lambda: io(lambda _: ...)(None), None),
    (lambda: io(lambda a, b, c: ...)(1, 2, 3), 1),
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


test_via_indexer = case_of(
    (lambda: via_indexer(lambda v: v + 3)[5], 8),
    (lambda: via_indexer(truediv)[8, 2], 4),
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
)


test_merged = case_of(
    (
        lambda: merged(lambda a: a - 1, lambda _: _, lambda a: a + 1)(2),
        (1, 2, 3),
    ),
)


@mark.parametrize(
    "factor, original_x, original_y, original_z",
    [
        (1, 2, 4, 4), (0.5, 4, 4, 12), (2, 8, 1, -78), (10, 12, 3, 12),
        (0, 1000, 2000, 3000), (100, 10, 10, 0), (-3, 2, -3, 14), (-1, -2, -3, -4)
    ]
)
def test_mergely_by_formula_function(
    factor: int | float,
    original_x: int | float,
    original_y: int | float,
    original_z: int | float,
):
    assert (
        mergely(
            lambda factor: (lambda x, y, z: factor * (x ** y + z)),
            lambda factor: factor * original_x,
            lambda factor: factor * original_y,
            lambda factor: factor * original_z,
        )(factor)
        == factor * (
            (factor * original_x) ** (factor * original_y) + (factor * original_z)
        )
    )
