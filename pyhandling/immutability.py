from copy import deepcopy, copy
from functools import wraps
from typing import Callable, Type, Any, Concatenate, Self

from pyhandling.annotations import ObjectT, P, ValueT, one_value_action
from pyhandling.atoming import atomically
from pyhandling.signature_assignmenting import calling_signature_of


__all__ = ("to_clone", "publicly_immutable", "property_to")


def to_clone(
    method: Callable[Concatenate[ObjectT, P], Any],
    deeply: bool = True,
) -> Callable[Concatenate[ObjectT, P], ObjectT]:
    """
    Decorator function to spawn new objects by cloning and applying an input
    method to them.

    Specifies the use of `copy` or `deepcopy` by `deeply` parameter.
    """

    @wraps(method)
    def wrapper(instance: ObjectT, *args: P.args, **kwargs: P.kwargs) -> ObjectT:
        clone = (deepcopy if deeply else copy)(instance)
        method(clone, *args, **kwargs)

        return clone

    wrapper.__signature__ = calling_signature_of(wrapper).replace(
        return_annotation=Self
    )

    return wrapper


def publicly_immutable(class_: Type[ValueT]) -> Type[ValueT]:
    """Decorator for an input class that forbids it change its public fields."""

    old_setattr = class_.__setattr__

    @wraps(old_setattr)
    def new_setattr(
        instance: object,
        attribute_name: str,
        attribute_value: Any,
    ) -> None:
        if attribute_name and attribute_name[0] != '_':
            raise AttributeError(
                f"cannot set '{attribute_name}' attribute of publicly immutable"
                f" type '{class_}'"
            )

        return old_setattr(instance, attribute_name, attribute_value)

    class_.__setattr__ = new_setattr

    return class_


@atomically
class property_to:
    """
    Descriptor that takes data from an attribute that already exists in an
    object.

    Has the ability to set a delegating attribute (Does not set by default).
    """

    def __init__(
        self,
        delegated_attribute_name: str,
        *,
        settable: bool = False,
        getting_converter: one_value_action = lambda value: value,
        setting_converter: one_value_action = lambda value: value
    ):
        self.delegated_attribute_name = delegated_attribute_name
        self.settable = settable
        self.getting_converter = getting_converter
        self.setting_converter = setting_converter

    def __get__(self, instance: object, owner: type) -> Any:
        return self.getting_converter(getattr(
            instance,
            self.delegated_attribute_name,
        ))

    def __set__(self, instance: object, value: Any) -> None:
        if not self.settable:
            raise AttributeError(
                f"delegating property of '{self.delegated_attribute_name}' for"
                f" '{type(instance).__name__}' object is not settable"
            )

        setattr(
            instance,
            self.delegated_attribute_name,
            self.setting_converter(value),
        )
