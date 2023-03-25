from functools import partial
from typing import Callable, Any

from pyhandling.synonyms import *
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import ArgumentPack
from tests.mocks import CustomContext

from pytest import mark, raises


test_returned = calling_test_case_of((lambda: returned(None), None))


test_raise_ = calling_test_case_of((
    lambda: with_context_by(lambda error: raises(type(error)), raise_)(Exception()),
    None,
))


test_assert_ = calling_test_case_of(
    (lambda: assert_(16), None),
    (
        lambda: with_context_by(lambda _: raises(AssertionError), assert_)(None),
        None,
    ),
)


test_with_positional_unpacking = calling_test_case_of((
    lambda: with_positional_unpacking(lambda a, b, c: (c, b, a), (1, 2, 3)),
    (3, 2, 1),
))


test_with_keyword_unpacking = calling_test_case_of((
    lambda: with_keyword_unpacking(lambda a, b, c: (c, b, a), dict(a=1, b=2, c=3)),
    (3, 2, 1),
))


test_bind = calling_test_case_of((
    lambda: bind(lambda a, b: a + b, 'b', 3)(1),
    4,
))


test_call = calling_test_case_of((
    lambda: call(lambda a, b: a / b, 1, 10),
    0.1,
))


test_getitem = calling_test_case_of((lambda: getitem(dict(a=1), 'a'), 1))


@mark.parametrize('object_, key, value', ((dict(), 'a', 1), (dict(), 'b', 2)))
def test_setitem(object_: object, key: Any, value: Any) -> None:
    setitem(object_, key, value)

    assert object_[key] == value


test_execute_operation = calling_test_case_of((
    lambda: execute_operation(200, '+', 56),
    256,
))


test_transform = calling_test_case_of(
    (lambda: transform(False, 'not'), True),
    (lambda: transform(-43, '~'), 42),
)


test_to_context = calling_test_case_of(
    (lambda: to_context(lambda _: _)(CustomContext(None)), None),
    (lambda: to_context(lambda n: n + 6)(CustomContext(10)), 16),
)