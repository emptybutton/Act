from functools import partial
from typing import Callable, Any

from pyhandling.synonyms import *
from pyhandling.testing import calling_test_of, calling_test_from
from pyhandling.tools import ArgumentPack
from tests.mocks import CustomContext

from pytest import mark, raises


def add_then_divide_by_zero_f_attribute(adding_number: int, object_: object) -> None:
    object_.f += adding_number
    object_.f /= 0
test_return_ = calling_test_of(return_, None, ArgumentPack.of(None))


test_raise_ = calling_test_of(
    with_context_by(lambda error: raises(type(error)), raise_),
    None,
    ArgumentPack.of(Exception())
)


test_assert_ = calling_test_from(
    (assert_, None, ArgumentPack.of(16)),
    (
        with_context_by(lambda _: raises(AssertionError), assert_),
        None,
        ArgumentPack.of(None)
    ),
)


test_positionally_unpack_to = calling_test_of(
    positionally_unpack_to,
    (3, 2, 1),
    ArgumentPack.of(lambda a, b, c: (c, b, a), (1, 2, 3))
)


test_unpack_by_keys_to = calling_test_of(
    unpack_by_keys_to,
    (3, 2, 1),
    ArgumentPack.of(lambda a, b, c: (c, b, a), dict(a=1, b=2, c=3))
)


test_bind = calling_test_of(
    bind,
    4,
    [ArgumentPack.of(lambda a, b: a + b, 'b', 3), ArgumentPack.of(1)]
)


test_call = calling_test_of(call, 0.1, ArgumentPack.of(lambda a, b: a / b, 1, 10))


test_getitem_of = calling_test_of(getitem_of, 1, ArgumentPack.of(dict(a=1), 'a'))


@mark.parametrize('object_, key, value', ((dict(), 'a', 1), (dict(), 'b', 2)))
def setitem_of(object_: object, key: Any, value: Any) -> None:
    setitem_of(object_, key, value)

    assert object_[key] == value


test_execute_operation = calling_test_of(
    execute_operation,
    256,
    ArgumentPack.of(200, '+', 56),
)


test_transform = calling_test_from(
    (transform, True, ArgumentPack.of(False, 'not')),
    (transform, 42, ArgumentPack.of(-43, '~')),
)


test_to_context = calling_test_from(
    (to_context(lambda _: _), None, ArgumentPack.of(CustomContext(None))),
    (to_context(lambda n: n + 6), 16, ArgumentPack.of(CustomContext(10))),
)