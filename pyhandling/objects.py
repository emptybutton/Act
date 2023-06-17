from functools import partial, reduce
from operator import or_
from types import MethodType
from typing import (
    Mapping, Callable, Self, Generic, Concatenate, Any, Optional, ClassVar
)
from sys import getrecursionlimit, setrecursionlimit

from pyannotating import Special

from pyhandling.annotations import K, V, Pm, R, O
from pyhandling.contexting import contextually, contexted, ContextRoot
from pyhandling.flags import flag_about, Flag
from pyhandling.immutability import to_clone
from pyhandling.partiality import partially, flipped
from pyhandling.tools import action_repr_of


__all__ = (
    "obj",
    "method_of",
    "dict_of",
    "of",
    "void",
)


def _with_recurion_limit(
    limit: int,
    action: Callable[Pm, R],
    *args: Pm.args,
    **kwargs: Pm.kwargs,
) -> R:
    old_limit = getrecursionlimit()

    setrecursionlimit(limit)
    result = action(*args, **kwargs)
    setrecursionlimit(old_limit)

    return result


class obj:
    """
    Constructor for objects that do not have a common structure.

    Creates an object with attributes from keyword arguments.

    When called with a `__call__` attribute, makes an output object callable on
    that attribute as a method.

    Can be obtained union of an instance with any other object via `&`.
    """

    plugin: ClassVar[Flag] = flag_about("flag_about")

    def __new__(
        cls,
        __call__: Optional[Callable[Concatenate[Self, Pm], R]] = None,
        **attributes: Special[ContextRoot[Callable[[Self, Any], Any], plugin]],
    ) -> "Special[_callable_obj[Pm, R], Self]":
        return (
            _callable_obj(__call__=__call__, **attributes)
            if __call__ is not None
            else super().__new__(cls)
        )

    def __init__(
        self,
        **attributes: Special[ContextRoot[Callable[[Self, str], Any], plugin]],
    ):
        self.__dict__ = {
            key: (
                contextually(*attr)(self, key)
                if contexted(attr).context == obj.plugin
                else attr
            )
            for key, attr in attributes.items()
        }

    def __repr__(self) -> str:
        return "<{}>".format(', '.join(
            f"{name}={self.__repr_of(value)}"
            for name, value in self.__dict__.items()
        ))

    @staticmethod
    def __repr_of(value: Any) -> str:
        try:
            return _with_recurion_limit(20, action_repr_of, value)
        except RecursionError:
            return '...'

    def __eq__(self, other: Special[Self]) -> bool:
        return isinstance(other, obj) and dict_of(self) == dict_of(other)

    def __and__(self, other: Special[Mapping]) -> Self:
        return obj.of(self, other)

    def __rand__(self, other: Special[Mapping]) -> Self:
        return obj.of(other, self)

    @to_clone
    def __add__(self, attr_name: str) -> Self:
        if not hasattr(self, attr_name):
            setattr(self, attr_name, None)

    @to_clone
    def __sub__(self, attr_name: str) -> Self:
        if hasattr(self, attr_name):
            delattr(self, attr_name)

    @classmethod
    def of(cls, *objects: Special[Mapping]) -> Self:
        """
        Constructor for data from other objects.

        When passing a dictionary without `__dict__`, gets data from that
        dictionary.

        Data of subsequent objects have higher priority than previous ones.
        """

        return obj(**reduce(or_, map(dict_of, objects)))


class _callable_obj(obj, Generic[Pm, R]):
    """Variation of `obj` for callability."""

    def __new__(cls, *args, **kwargs) -> Self:
        return object.__new__(cls)

    def __init__(self, __call__: Callable[Concatenate[Self, Pm], R], **attributes):
        super().__init__(**attributes)
        self.__call__ = __call__

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return (
            self.__call__
            if isinstance(self.__call__, staticmethod)
            else partial(self.__call__, self)
        )(*args, **kwargs)


def method_of(method: Callable[[obj, ...], Any]) -> contextually[
    Callable[[Any, Any], MethodType],
    obj.plugin,
]:
    """Constructor for `obj` plugin that adds an input method to it."""

    return contextually(lambda object_, _: MethodType(method, object_), obj.plugin)


def dict_of(value: Special[Mapping[K, V]]) -> dict[K, V]:
    """
    Function to safely read from `__dict__` attribute.

    Returns an empty `dict` when an input value has no a `__dict__` attribute
    or casts it to a `dict`, when passing a `Mapping` object.
    """

    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    elif isinstance(value, Mapping):
        return dict(**value)
    else:
        return dict()


@partially
@flipped
@to_clone
def of(object_: O, data: Special[Mapping], /) -> O:
    """
    Function to set all attributes of a first input object to a clone of a
    second input object.
    """

    object_.__dict__ = dict_of(object_) | dict_of(data)


void = obj()  # Object without data
