from copy import deepcopy, copy
from functools import wraps
from typing import Callable, Any, Concatenate, Self

from pyhandling.annotations import V, Pm, one_value_action, TypeT
from pyhandling.atoming import atomically
from pyhandling.partials import partially
from pyhandling.signature_assignmenting import call_signature_of


__all__ = ("to_clone", "publicly_immutable", "property_to")


@partially
def to_clone(
    method: Callable[Concatenate[V, Pm], Any],
    *,
    deep: bool = False,
) -> Callable[Concatenate[V, Pm], V]:
    """
    Decorator function to spawn new objects by cloning and applying an input
    method to them.

    Specifies the use of `copy` or `deepcopy` by `deep` parameter.
    """

    @wraps(method)
    def wrapper(instance: V, *args: Pm.args, **kwargs: Pm.kwargs) -> V:
        clone = (deepcopy if deep else copy)(instance)
        method(clone, *args, **kwargs)

        return clone

    wrapper.__signature__ = call_signature_of(wrapper).replace(
        return_annotation=Self
    )

    return wrapper


def publicly_immutable(class_: TypeT) -> TypeT:
    """
    Decorator for an input class that forbids it change its public attributes.
    Public attributes are those whose names do not start with `_`.
    """

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

    Has the ability to set a delegating attribute (Does not set by default) and
    additional layers of transformation that data passes through when it is
    received or set.
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
