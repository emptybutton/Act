from typing import Iterable, Callable, Any

from pytest import mark, fail, raises

from pyhandling.testing import calling_test_case_of
from pyhandling.immutability import *
from pyhandling.tools import with_attributes


def test_to_clone():
    object_ = with_attributes(mock_attribute=42)

    cloned_object = to_clone(setattr)(object_, 'mock_attribute', 4)

    assert object_ is not cloned_object
    assert object_.mock_attribute == 42
    assert cloned_object.mock_attribute == 4


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


@mark.parametrize(
    'delegating_property_kwargs, is_waiting_for_attribute_setting_error',
    [
        (dict(), True),
        (dict(settable=True), False),
        (dict(settable=True), False)
    ]
)
def test_delegating_property_getting(
    delegating_property_kwargs: dict,
    is_waiting_for_attribute_setting_error: bool,
    delegating_property_delegated_attribute_name: str = '_some_attribue'
):
    mock = with_attributes(**{delegating_property_delegated_attribute_name: 0})

    property_ = property_to(
        delegating_property_delegated_attribute_name,
        **delegating_property_kwargs
    )

    try:
        property_.__set__(mock, 42)
    except AttributeError as error:
        if not is_waiting_for_attribute_setting_error:
            raise error

    assert (
        getattr(mock, delegating_property_delegated_attribute_name)
        == property_.__get__(mock, type(mock))
    )