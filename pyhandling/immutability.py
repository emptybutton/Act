from copy import deepcopy, copy
from functools import wraps
from typing import NoReturn, Callable, Any, Concatenate, Self

from pyhandling.annotations import V, Pm, TypeT
from pyhandling.errors import InvalidInitializationError
from pyhandling.partiality import partially
from pyhandling.signatures import call_signature_of


__all__ = ("NotInitializable", "to_clone", "publicly_immutable")


class NotInitializable:
    """Mixin class preventing instantiation."""

    def __init__(self, *args, **kwargs) -> NoReturn:
        raise InvalidInitializationError(
            f"\"{type(self).__name__}\" type object cannot be initialized"
        )


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
