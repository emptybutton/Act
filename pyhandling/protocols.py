from typing import runtime_checkable, Protocol, Optional, Callable

from pyannotating import Special

from pyhandling.annotations import P, V, TypeT
from pyhandling.immutability import to_clone
from pyhandling.objects import Unia, namespace_of
from pyhandling.partials import partially


__all__ = (
    "Variable",
    "Protocolable",
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

    Exists to describe results of `protocoled` functions.
    """

    __protocol__: P


@namespace_of
class protocoled:
    """
    Callable namespace for functions that create a protocol based on an input
    value and immutably add that protocol to an input value.

    Adds a generated protocol to the `__protocol__` attribute, making an output
    value `Protocolable`.

    Can create a protocol based on an input value (`from_value`) or based on
    a type (`from_type`), but in this case, this protocol describes values
    created from the described type, but not the type itself.

    When calling the namespace itself from a type, it selects the method of
    protocoling instances of this type (`from_type`), in other cases, an input
    value itself (`from_value`).
    """

    @partially
    def __call__(
        value: Special[type, V],
        *,
        deep: Optional[bool] = None,
    ) -> Unia[V, Protocolable] | Callable[[Special[type, V]], Unia[V, Protocolable]]:
        if isinstance(value, type) and deep is None:
            return protocoled.from_type(value)
        elif deep is None:
            return protocoled.from_value(value)
        else:
            return protocoled.from_value(value, deep=deep)

    @partially
    @to_clone
    def from_value(value: V, *, deep: bool = False) -> Unia[V, Protocolable]:
        value.__protocol__ = runtime_checkable(type(
            f"{value.__class__}ObjectProtocol",
            (Protocol, ),
            dict.fromkeys(dir(value), key=None) if deep else value.__dict__,
        ))

    @to_clone
    def from_type(type_: TypeT) -> Unia[TypeT, Protocolable]:
        type_.__protocol__ = runtime_checkable(type(
            f"{type_.__name__}Protocol",
            (type_, Protocol),
            dict(),
        ))
