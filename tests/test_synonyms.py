from functools import partial
from typing import Callable, Any

from pyhandling.synonyms import return_, raise_, call, call_method, getattr_of, setattr_of, getitem_of, setitem_of, execute_operation, handle_context_by, transform_by, assert_
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


@mark.parametrize('func, result', ((partial(return_, 1), 1), (lambda: 1 + 2, 3)))
def test_call(func: Callable[[], Any], result: Any):
    assert call(func) == result


@mark.parametrize('result, object_, method_name', (('<Box instance>', Box(), '__repr__'), ))
def test_call_method(result: Any, object_: object, method_name: str):
    assert call_method(object_, method_name) == result


@mark.parametrize('object_, attribute_name, result', ((Box(a=1), 'a', 1), (Box(b=2), 'b', 2)))
def test_getattr_of(object_: object, attribute_name: str, result: Any):
    assert getattr_of(object_, attribute_name) == result


@mark.parametrize('object_, attribute_name, attribute_value', ((Box(), 'a', 1), (Box(), 'b', 2)))
def test_setattr_of(object_: object, attribute_name: str, attribute_value: Any):
    setattr_of(object_, attribute_name, attribute_value)

    assert getattr(object_, attribute_name) == attribute_value


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
