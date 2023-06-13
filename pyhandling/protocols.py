from typing import runtime_checkable, Protocol

from pyhandling.annotations import P, V
from pyhandling.immutability import to_clone, NotInitializable
from pyhandling.objects import Unia, dict_of


__all__ = (
    "Variable",
    "Protocolable",
    "Proto",
    "protocol_of",
    "protocoled",
)


@runtime_checkable
class Variable(Protocol):
    """
    Protocol describing objects capable of checking another object against a
    subvariant of the describing object (`isinstance(another, describing)`).
    """

    def __instancecheck__(self, instance: object) -> bool:
        ...


@runtime_checkable
class Protocolable(Protocol[P]):
    """
    Protocol for objects that have a reference to a protocol previously based
    on this object.
    """

    __protocol__: P


class Proto(NotInitializable):
    """
    Annotation of input value protocol or annotation-like access to
    `__protocol__` attribute.
    """

    def __class_getitem__(self, value: Protocolable[P]) -> P:
        return value.__protocol__


def protocol_of(value: V) -> Protocol:
    """Function to create a protocol based on an input value."""

    return runtime_checkable(type(
        "{}Protocol".format(
            value.__name__
            if isinstance(value, type)
            else f"{type(value).__name__}Instance"
        ),
        (Protocol, ),
        dict_of(value),
    ))


@to_clone
def protocoled(value: V) -> Unia[V, Protocolable]:
    """
    Function to create a protocol based on an input value and immutably add that
    protocol to an input value.

    Adds a generated protocol to the `__protocol__` attribute, making an output
    value `Protocolable`.
    """

    value.__protocol__ = protocol_of(value)
