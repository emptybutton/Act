from typing import Iterable, Callable, Any

from pytest import mark, fail, raises

from pyhandling.tools import *
from tests.mocks import with_attributes


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
    'args, kwargs',
    [
        ((1, 2, 3), dict(a=4, b=5, c=6)),
        ((1, ), dict(a=4, b=5, c=6)),
        (tuple(), dict(a=4, b=5, c=6)),
        ((1, 2, 3), dict()),
        (tuple(), dict()),
    ]
)
def test_argument_pack_creation_via_call(args: Iterable, kwargs: dict):
    assert ArgumentPack.of(*args, **kwargs) == ArgumentPack(args, kwargs)


@mark.parametrize(
    'first_args, first_kwargs, second_args, second_kwargs',
    [
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), tuple(), dict(d=7, e=8, f=9)),
        ((1, 2, 3), dict(), (4, 5, 6), dict()),
        (tuple(), dict(), ) * 2,
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(a=7, b=8, c=9)),
    ]
)
def test_argument_pack_merger(
    first_args: Iterable,
    first_kwargs: dict,
    second_args: Iterable,
    second_kwargs: dict
):
    assert (
        ArgumentPack(first_args, first_kwargs).merge_with(ArgumentPack(second_args, second_kwargs))
        == ArgumentPack.of(*first_args, *second_args, **(first_kwargs | second_kwargs))
    )


@mark.parametrize(
    'first_args, first_kwargs, second_args, second_kwargs',
    [
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), tuple(), dict(d=7, e=8, f=9)),
        ((1, 2, 3), dict(), (4, 5, 6), dict()),
        (tuple(), dict(), ) * 2,
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(a=7, b=8, c=9)),
    ]
)
def test_argument_pack_expanding(
    first_args: Iterable,
    first_kwargs: dict,
    second_args: Iterable,
    second_kwargs: dict
):
    assert (
        ArgumentPack(first_args, first_kwargs).expand_with(*second_args, **second_kwargs)
        == ArgumentPack.of(*first_args, *second_args, **(first_kwargs | second_kwargs))
    )


@mark.parametrize(
    'func, argument_pack, result',
    [
        (lambda a, b, c: a * b * c, ArgumentPack((1, 2, 3)), 6),
        (lambda a, b, c: a + b + c, ArgumentPack((8, 4), dict(c=30)), 42),
        (lambda a, b, c: a ** b ** c, ArgumentPack(kwargs=dict(a=2, b=2, c=3)), 256),
        (lambda: 48, ArgumentPack(), 48),
    ]
)
def test_argument_pack_calling(func: Callable, argument_pack: ArgumentPack, result: Any):
    assert argument_pack.call(func) == result


@mark.parametrize(
    'argument_pack, argument_key, result',
    [
        (ArgumentPack((1, 2, 3)), ArgumentKey(0), 1),
        (ArgumentPack((2, 8, 32, 64, 128), dict(a=1)), ArgumentKey(3), 64),
        (ArgumentPack((4, 2), dict(a=32, b=64, c=128)), ArgumentKey('c', is_keyword=True), 128),
        (ArgumentPack(kwargs=dict(a=1, b=5, c=7)), ArgumentKey('b', is_keyword=True), 5),
    ]
)
def test_argument_pack_getting_argument_by_key(
    argument_pack: ArgumentPack,
    argument_key: ArgumentKey,
    result: Any
):
    assert argument_pack[argument_key] == result


@mark.parametrize(
    "documentation",
    (
        "Is a handler.", "Is a checker.", "Something.", str(),
        "\n\tIs something.\n\tOr not?", "\tIs a handler.\n\tIs a handler",
    )
)
def test_documenting_by(documentation: str):
    mock = with_attributes()

    documenting_by(documentation)(mock)

    assert '__doc__' in mock.__dict__.keys()
    assert mock.__doc__ == documentation


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

    property_ = DelegatingProperty(
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


@mark.parametrize(
    'clock, ticks_to_subtract, result_ticks',
    [
        (Clock(0), 0, 0),
        (Clock(10), 3, 7),
        (Clock(30), -12, 42),
        (Clock(-5), 3, -8),
        (Clock(-40), -8, -32),
    ]
)
def test_clock(clock: Clock, ticks_to_subtract: int, result_ticks: int):
    initual_ticks = clock.initial_ticks_to_disability

    clock.ticks_to_disability -= ticks_to_subtract

    assert clock.initial_ticks_to_disability == initual_ticks
    assert clock.ticks_to_disability == result_ticks


@mark.parametrize(
    'args, kwargs, result_argument_pack',
    [
        ((1, 2, 3), dict(), ArgumentPack((1, 2, 3))),
        ((8, 32, 64), dict(a=1, b=2, c=3), ArgumentPack((8, 32, 64), dict(a=1, b=2, c=3))),
        (tuple(), dict(x=16, y=4, z=1), ArgumentPack(kwargs=dict(x=16, y=4, z=1))),
        (tuple(), dict(), ArgumentPack()),
        ((42, ), dict(x=16), ArgumentPack((42, ), dict(x=16))),
        ((42, ), dict(), ArgumentPack((42, ))),
        ((ArgumentPack((42, )), ), dict(), ArgumentPack((42, ))),
        ((ArgumentPack((42, ), dict(a=32)), ), dict(), ArgumentPack((42, ), dict(a=32))),
    ]
)
def test_as_argument_pack(args: Iterable, kwargs: dict, result_argument_pack: ArgumentPack):
    assert as_argument_pack(*args, **kwargs) == result_argument_pack



@mark.parametrize(
    'input_collection, result_collection',
    [
        ([1, 2, 3], (1, 2, 3)),
        ([1, 2, (3, 4)], (1, 2, 3, 4)),
        ([1, 2, (3, (4, 5))], (1, 2, 3, (4, 5))),
        (tuple(), tuple()),
        (str(), tuple()),
    ]
)
def test_open_collection_items(input_collection: Iterable, result_collection: tuple):
    assert open_collection_items(input_collection) == result_collection


@mark.parametrize(
    'resource, result_collection',
    [
        (42, (42, )),
        (str(), (str(), )),
        (tuple(), (tuple(), )),
        ((1, 2, 3), ((1, 2, 3), ))
    ]
)
def test_wrap_in_collection(resource: Any, result_collection: tuple):
    assert wrap_in_collection(resource) == result_collection