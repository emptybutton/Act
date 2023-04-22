from functools import partial
from typing import Callable, Any, Iterable, Type

from pyhandling.arguments import ArgumentPack
from pyhandling.synonyms import *
from pyhandling.testing import calling_test_case_of
from tests.mocks import CustomContext, fail_by_error

from pytest import mark, raises


test_returned = calling_test_case_of((lambda: returned(None), None))


test_raise_ = calling_test_case_of((
    lambda: with_context_manager_by(lambda error: raises(type(error)), raise_)(Exception()),
    None,
))


test_assert_ = calling_test_case_of(
    (lambda: assert_(16), None),
    (
        lambda: with_context_manager_by(lambda _: raises(AssertionError), assert_)(None),
        None,
    ),
)


test_collection_of = calling_test_case_of(
    (lambda: collection_of(1, 2, 3), (1, 2, 3)),
    (lambda: collection_of(), tuple()),
)


test_on = calling_test_case_of(
    (lambda: on(lambda x: x > 0, lambda x: x ** x)(4), 256),
    (lambda: on(lambda x: x > 0, lambda x: x ** x)(-4), -4),
    (lambda: on(lambda x: x > 0, lambda x: x ** x)(-4), -4),
    (lambda: on(lambda x: x > 0, lambda _: _, else_=lambda x: -x)(4), 4),
    (lambda: on(lambda x: x > 0, lambda _: _, else_=lambda x: -x)(-4), 4),
)


test_trying_to_without_error = calling_test_case_of(
    (lambda: trying_to(lambda a: 1 / a, fail_by_error)(10), 0.1),
    (lambda: trying_to(lambda a, b: a + b, fail_by_error)(5, 3), 8),
    (lambda: trying_to(lambda a, b: a + b, fail_by_error)(5, b=3), 8),
    (lambda: trying_to(lambda: 256, fail_by_error)(), 256),
)


@mark.parametrize(
    "func, input_args, error_type",
    [
        (lambda x: x / 0, (42, ), ZeroDivisionError),
        (lambda x, y: x + y, (1, '2'), TypeError),
        (lambda mapping, key: mapping[key], (tuple(), 0), IndexError),
        (lambda mapping, key: mapping[key], (tuple(), 10), IndexError),
        (lambda mapping, key: mapping[key], ((1, 2), 2), IndexError),
        (lambda mapping, key: mapping[key], (dict(), 'a'), KeyError),
        (lambda mapping, key: mapping[key], ({'a': 42}, 'b'), KeyError),
        (lambda: int('1' + '0'*4300), tuple(), ValueError)
    ]
)
def test_trying_to_with_error(
    func: Callable,
    input_args: Iterable,
    error_type: Type[Exception]
):
    assert type(trying_to(func, lambda error: error)(*input_args)) is error_type



test_with_unpacking = calling_test_case_of((
    lambda: with_unpacking(lambda a, b, c: (c, b, a))([1, 2, 3]),
    (3, 2, 1),
))


test_with_keyword_unpacking = calling_test_case_of((
    lambda: with_keyword_unpacking(lambda a, b, c: (c, b, a))(dict(a=1, b=2, c=3)),
    (3, 2, 1),
))


test_to_context_manager = calling_test_case_of(
    (lambda: to_context_manager(lambda _: _)(CustomContext(None)), None),
    (lambda: to_context_manager(lambda n: n + 6)(CustomContext(10)), 16),
)