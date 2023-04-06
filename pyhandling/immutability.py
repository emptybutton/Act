from functools import wraps
from typing import Callable, Type, Any, Concatenate

from pyhandling.annotations import ObjectT, P, ValueT, one_value_action


__all__ = ("to_clone", "publicly_immutable", "property_of")


def to_clone(method: Callable[Concatenate[ObjectT, P], Any]) -> Callable[Concatenate[ObjectT, P], ObjectT]:
    """
    Decorator function to spawn new objects by cloning and applying an input
    method to them.
    """

    @wraps(method)
    def wrapper(instance: ObjectT, *args: P.args, **kwargs: P.kwargs) -> ObjectT:
        clone = deepcopy(instance)
        method(clone, *args, **kwargs)

        return clone

    wrapper.__annotations__["return"] = Self

    return wrapper


def publicly_immutable(class_: Type[ValueT]) -> Type[ValueT]:
    """Decorator for an input class that forbids it change its public fields."""

    old_setattr = class_.__setattr__

    @wraps(old_setattr)
    def new_setattr(instance: object, attribute_name: str, attribute_value: Any) -> None:
        if attribute_name and attribute_name[0] != '_':
            raise AttributeError(
                f"cannot set '{attribute_name}' attribute of publicly immutable type '{class_}'"
            )

        return old_setattr(instance, attribute_name, attribute_value)

    class_.__setattr__ = new_setattr

    return class_


class property_of:
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
        return self.getting_converter(getattr(instance, self.delegated_attribute_name))

    def __set__(self, instance: object, value: Any) -> None:
        if not self.settable:
            raise AttributeError(
                "delegating property of '{attribute_name}' for '{class_name}' object is not settable".format(
                    attribute_name=self.delegated_attribute_name,
                    class_name=type(instance).__name__
                )
            )

        setattr(instance, self.delegated_attribute_name, self.setting_converter(value))