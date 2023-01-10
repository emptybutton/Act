from typing import Iterable, Callable

from pytest import mark

from pyhandling.tools import to_clone, ArgumentPack, ArgumentKey, DelegatingProperty


class MockObject:
    def __init__(self, **attributes):
        self.__dict__ = attributes

    def __repr__(self) -> str:
        return "<MockObject with {attributes}>".format(
            attributes=str(self.__dict__)[1:-1].replace(': ', '=').replace('\'', '')
        )


def test_to_clone():
    object_ = MockObject(mock_attribute=42)

    cloned_object = to_clone(setattr)(object_, 'mock_attribute', 4)

    assert object_ is not cloned_object
    assert object_.mock_attribute == 42
    assert cloned_object.mock_attribute == 4


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
    assert ArgumentPack.create_via_call(*args, **kwargs) == ArgumentPack(args, kwargs)
