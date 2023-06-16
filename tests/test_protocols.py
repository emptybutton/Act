from dataclasses import dataclass, field

from pyhandling.objects import obj
from pyhandling.protocols import *
from pyhandling.testing import case_of


test_protocol_of = case_of(
    (lambda: isinstance(obj(a=1), protocol_of(obj(a=..., b=...))), False),
    (lambda: isinstance(obj(a=1, b=2), protocol_of(obj(a=..., b=...))), True),
    (lambda: isinstance(obj(a=1, b=2, c=3), protocol_of(obj(a=..., b=...))), True),
)


test_protocoled = case_of(
    (
        lambda: isinstance(obj(a=1), protocoled(obj(a=..., b=...)).__protocol__),
        False,
    ),
    (
        lambda: isinstance(
            obj(a=1, b=2),
            protocoled(obj(a=..., b=...)).__protocol__,
        ),
        True,
    ),
    (
        lambda: isinstance(
            obj(a=1, b=2, c=3),
            protocoled(obj(a=..., b=...)).__protocol__,
        ),
        True
    ),
)


test_protocolable = case_of(
    (lambda: isinstance(protocoled(obj(a=1, b=2)), Protocolable), True),
    (lambda: isinstance(obj(a=1, b=2), Protocolable), False),
)


def test_proto():
    object_ = protocoled(obj(a=1, b=2))

    assert Proto[object_] == object_.__protocol__


def test_protocoled_classes():
    class A:
        a = 1

    @protocoled
    class B(A):
        b = 2

    instance = B()

    assert instance.a == 1
    assert instance.b == 2

    assert isinstance(B, Protocolable)

    assert not isinstance(obj(a=1), B.__protocol__)
    assert isinstance(obj(a=1, b=2), B.__protocol__)
    assert isinstance(obj(a=1, b=2, c=3), B.__protocol__)


def test_protocoled_dataclasses():
    @dataclass(frozen=True)
    class A:
        a: int

    @protocoled
    @dataclass(frozen=True)
    class B(A):
        b: int = field(default_factory=lambda: 4)

    instance = B(a=1, b=2)

    assert instance.a == 1
    assert instance.b == 2

    assert isinstance(B, Protocolable)

    assert not isinstance(obj(a=1), B.__protocol__)
    assert isinstance(obj(a=1, b=2), B.__protocol__)
    assert isinstance(obj(a=1, b=2, c=3), B.__protocol__)
