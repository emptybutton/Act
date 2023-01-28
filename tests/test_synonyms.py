from functools import partial
from typing import Callable, Any

from pyhandling.synonyms import *
from tests.mocks import Box

from pytest import mark, raises


def add_then_divide_by_zero_f_attribute(adding_number: int, object_: object) -> None:
    object_.f += adding_number
    object_.f /= 0


@mark.parametrize('resource', (0, 1, 2))
def test_return_(resource: Any):
    assert return_(resource) == resource


@mark.parametrize('error', (Exception, ))
def test_raise_(error: Exception):
    with raises(error):
        raise_(error)


@mark.parametrize('resource', (True, 42j, b"Hello world!", [1, 2, 3]))
def test_error_free_assert_(resource: Any):
    assert_(resource)


@mark.parametrize('resource', (False, int(), str(), tuple()))
def test_assert_error_raising(resource: Any):
    with raises(AssertionError):
        assert_(resource)


def test_positionally_unpack_to():
    assert positionally_unpack_to(lambda a, b, c: (c, b, a), (1, 2, 3)) == (3, 2, 1)


def test_unpack_by_keys_to():
    assert unpack_by_keys_to(lambda a, b, c: (c, b, a), dict(a=1, b=2, c=3)) == (3, 2, 1)


def test_bind():
    func_to_bind = lambda first, second: first + second

    assert bind(func_to_bind, 'second', 3)(1) == func_to_bind(1, second=3)


@mark.parametrize('func, result', ((partial(return_, 1), 1), (lambda: 1 + 2, 3)))
def test_call(func: Callable[[], Any], result: Any):
    assert call(func) == result


@mark.parametrize('object_, key, result', ((dict(a=1), 'a', 1), (dict(b=2), 'b', 2)))
def test_getitem_of(object_: object, key: Any, result: Any) -> Any:
    assert getitem_of(object_, key) == result


@mark.parametrize('object_, key, value', ((dict(), 'a', 1), (dict(), 'b', 2)))
def setitem_of(object_: object, key: Any, value: Any) -> None:
    setitem_of(object_, key, value)

    assert object_[key] == value


@mark.parametrize('first, operator, second, result', ((1, '+', 2, 3), (2, '-', 1, 1), (4, '**', 4, 256)))
def test_execute_operation(first: Any, operator: str, second: Any, result: Any):
    assert execute_operation(first, operator, second) == result


@mark.parametrize(
    'operator, operand, result',
    [
        ('not', True, False),
        ('not', False, True),
        ('not', tuple(), True),
        ('~', -43, 42),
        ('~', 0, -1)
    ]
)
def test_transform(operator: str, operand: Any, result: Any):
    assert transform(operand, operator) == result


@mark.parametrize(
    'context_factory, context_handler, result', (
        (Box, lambda resource: resource, None),
        (partial(Box, 1), lambda resource: resource, 1),
        (partial(Box, 2), lambda number: number * 2, 4)
    )
)
def test_handle_context_by(
    context_factory: Callable[[], Any],
    context_handler: Callable[[Any], Any],
    result: Any
):
    assert handle_context_by(context_factory, context_handler) == result
