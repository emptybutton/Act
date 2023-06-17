from functools import reduce, partial
from operator import or_, attrgetter

from typing import runtime_checkable, Protocol

from pyhandling.annotations import P, V, Unia
from pyhandling.immutability import to_clone, NotInitializable
from pyhandling.objects import dict_of


__all__ = (
    "Variable",
    "Hashable",
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
class Hashable(Protocol):
    """Protocol for objects from which to get their hash."""

    def __hash__(self) -> int:
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

    return (
        runtime_checkable(type(
            f"{value.__name__}Protocol",
            (Protocol, ),
            (
                dict.fromkeys(
                    partial(reduce, or_)(reversed(tuple(map(
                        attrgetter("__annotations__"),
                        value.__mro__[:-1],
                    )))).keys(),
                    Ellipsis,
                )
                if "__dataclass_params__" in dict_of(value).keys()
                else reduce(or_, reversed(tuple(map(dict_of, value.__mro__[:-1]))))
            )
        ))
        if isinstance(value, type)
        else runtime_checkable(type(
            f"{type(value).__name__}InstanceProtocol",
            (Protocol, ),
            dict_of(value),
        ))
    )


@to_clone
def protocoled(value: V) -> Unia[V, Protocolable]:
    """
    Function to create a protocol based on an input value and immutably add that
    protocol to an input value.

    Adds a generated protocol to the `__protocol__` attribute, making an output
    value `Protocolable`.
    """

    value.__protocol__ = protocol_of(value)
