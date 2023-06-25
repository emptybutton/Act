from operator import setitem
from typing import Any

from pytest import raises

from act.errors import InvalidInitializationError
from act.immutability import *
from act.objects import obj


def test_not_initializable():
    class Some(NotInitializable):
        ...

    with raises(InvalidInitializationError):
        Some()


def test_to_clone():
    object_ = obj(mock_attribute=42)

    cloned_object = to_clone(setattr)(object_, 'mock_attribute', 4)

    assert object_ is not cloned_object
    assert object_.mock_attribute == 42
    assert cloned_object.mock_attribute == 4


def test_deep_to_clone():
    object_ = [[1, 2], 3, 4]

    cloned_object = to_clone(setitem, deep=True)(object_, 1, 16)

    assert object_ is not cloned_object

    assert object_ == [[1, 2], 3, 4]
    assert cloned_object == [[1, 2], 16, 4]

    assert object_[0] is not cloned_object[0]


def test_publicly_immutable():
    @publicly_immutable
    class SomeImmutable:
        def __init__(self, attr: Any):
            self._attr = attr
            self.__attr = attr

        @property
        def attr(self) -> Any:
            return self._attr

    some_immutable = SomeImmutable(16)

    assert some_immutable.attr == 16

    with raises(AttributeError):
        some_immutable.attr = 256
