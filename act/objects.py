from abc import ABC, abstractmethod
from copy import copy
from functools import reduce
from operator import or_
from types import MethodType
from typing import (
    Mapping, Callable, Self, Generic, Concatenate, Any, Optional, ClassVar,
    Tuple, TypeVar
)

from pyannotating import Special

from act.annotations import K, V, Pm, R, O, Union
from act.contexting import (
    contextually, contexted, contextualizing, as_
)
from act.data_flow import mergely, by, returnly
from act.errors import ObjectTemplateError
from act.flags import flag_about, Flag
from act.immutability import to_clone
from act.partiality import partially, flipped, partial
from act.pipeline import then
from act.representations import code_like_repr_of
from act.synonyms import on, returned
from act.signatures import call_signature_of
from act.tools import LeftCallable


__all__ = (
    "as_method",
    "obj",
    "temp",
    "dict_of",
    "hash_of",
    "of",
    "void",
    "like",
    "to_attribute",
)


as_method = contextualizing(flag_about("as_method"), to=contextually)


class _Arbitrary(ABC):
    _default_attribute_value: TypeVar

    def __init__(self, **attributes):
        self.__dict__ = {
            _: type(self)._for_setting(attr)
            for _, attr in attributes.items()
        }

    @abstractmethod
    def __instancecheck__(self, instance: Any) -> bool:
        ...

    def __repr__(self) -> str:
        return "<{}>".format(', '.join(
            (
                f"{name}"
                f"{type(self)._field_repr_of('<...>' if value is self else value)}"
            )
            for name, value in self.__dict__.items()
        ))

    def __hash__(self) -> int:
        return hash(type(self)) + _table_hash_of(dict_of(self))

    def __eq__(self, other: Special[Self]) -> bool:
        return dict_of(self) == dict_of(other)

    @to_clone
    def __add__(self, attr_name: str) -> Self:
        if not hasattr(self, attr_name):
            setattr(self, attr_name, type(self)._default_attribute_value)

    @to_clone
    def __sub__(self, attr_name: str) -> Self:
        if hasattr(self, attr_name):
            delattr(self, attr_name)

    def __and__(self, other: Special[Mapping]) -> Self:
        return obj.of(self, other)

    def __rand__(self, other: Special[Mapping]) -> Self:
        return obj.of(other, self)

    def __or__(self, other: Any):
        return Union[self, other]

    def __ror__(self, other: Any):
        return Union[other, self]

    @staticmethod
    @abstractmethod
    def _for_setting(value: Any) -> Any:
        ...

    @staticmethod
    @abstractmethod
    def _field_repr_of(value: Any) -> str:
        ...

    @classmethod
    def of(cls, *objects: Special[Mapping]) -> Self:
        """
        Constructor for data from other objects.

        When passing a dictionary without `__dict__`, gets data from that
        dictionary.

        Data of subsequent objects have higher priority than previous ones.
        """

        return cls(**reduce(or_, map(dict_of, objects)))


_to_fill = contextualizing(flag_about("_to_fill"))
_filled = contextualizing(flag_about("_filled"))

_of_temp = _to_fill | _filled

_NO_VALUE = flag_about("_NO_VALUE")


class obj(_Arbitrary):
    """
    Constructor for objects that do not have a common structure.

    Creates an object with attributes from keyword arguments.

    When called with a `__call__` attribute, makes an output object callable on
    that attribute as a method.

    Can be obtained union of an instance with any other object via `&`.
    """

    _default_attribute_value = None

    def __new__(
        cls,
        *,
        __call__: Callable[Concatenate[Self, Pm], R] | _NO_VALUE = _NO_VALUE,
        **attributes: Special[as_method[Callable[[Self, Any], Any]] | _to_fill[Any]],
    ) -> "Special[_callable_obj[Pm, R] | temp, Self]":
        complete_attributes = (
            attributes
            | (dict() if __call__ is _NO_VALUE else dict(__call__=__call__))
        )

        if any(contexted(attr).context == _of_temp for attr in attributes.values()):
            return temp(**{
                _: temp._unit_of(attr) for _, attr in complete_attributes.items()
            })

        return (
            _callable_obj(**complete_attributes)
            if __call__ is not _NO_VALUE and cls is obj
            else super().__new__(cls)
        )

    def __getattribute__(self, attr_name: str) -> Any:
        value = object.__getattribute__(self, attr_name)
        action, context = contexted(value)

        return MethodType(action, self) if context == as_method else value

    def __instancecheck__(self, instance: Any) -> bool:
        return all(
            hasattr(instance, name) and getattr(instance, name) == attr
            for name, attr in dict_of(self).items()
        )

    @staticmethod
    def _for_setting(value: V) -> V:
        return value

    @staticmethod
    def _field_repr_of(value: Any) -> str:
        return f"={code_like_repr_of(value)}"


class _callable_obj(obj, LeftCallable, Generic[Pm, R]):
    """Variation of `obj` for callability."""

    def __init__(
        self,
        *,
        __call__: Callable[Concatenate[Self, Pm], R],
        **attributes,
    ):
        super().__init__(**attributes | dict(__call__=__call__))

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self.__call__(*args, **kwargs)

    def __getattribute__(self, attr_name: str) -> Any:
        return (
            call_signature_of(self.__call__)
            if attr_name == "__signature__"
            else super().__getattribute__(attr_name)
        )


class temp(_Arbitrary, LeftCallable):
    _default_attribute_value = Any

    def __repr__(self) -> str:
        return super().__repr__() if dict_of(self) else f"{type(self).__name__}()"

    def __call__(self, *attrs, **kwattrs) -> obj:
        names_to_fill = tuple(
            name
            for name, value in self.__dict__.items()
            if value.context == _to_fill
        )

        entered_values_count = len(attrs) + len(kwattrs.keys())

        if len(names_to_fill) != entered_values_count:
            raise ObjectTemplateError(
                f"{len(names_to_fill)} values are needed to create an object"
                f" from a template, {entered_values_count} are entered"
            )

        return obj.of(
            {
                name: kwattrs[name] if name in kwattrs.keys() else attrs[index]
                for index, name in enumerate(names_to_fill)
            }
            | {
                name: form.value
                for name, form in self.__dict__.items()
                if name not in names_to_fill
            }
        )

    def __instancecheck__(self, instance: Any) -> bool:
        return all(
            (
                (
                    hasattr(instance, name)
                    and attr.value == getattr(instance, name)
                )
                if attr.context == _filled
                else hasattr(instance, name)
            )
            for name, attr in dict_of(self).items()
        )

    @staticmethod
    def _unit_of(value: V) -> _to_fill[V] | _filled[V]:
        return (
            value
            if contexted(value).context == _to_fill
            else as_(_filled, value)
        )

    @staticmethod
    def _for_setting(value: V) -> _filled[V] | _to_fill[V]:
        return (
            value
            if contexted(value).context == _filled
            else as_(_to_fill, value)
        )

    @staticmethod
    def _field_repr_of(value: Any) -> str:
        stored_value, context = contexted(value)

        if context is _to_fill:
            return f": {code_like_repr_of(stored_value)}"
        elif context == _filled:
            return f"={code_like_repr_of(stored_value)}"
        elif context == as_method:
            return f"()={code_like_repr_of(stored_value)}"
        else:
            return f"={code_like_repr_of(value)}"


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


def hash_of(value: Any) -> int:
    """Function to get hash of any object."""

    return hash(value) if hasattr(value, "__hash__") else id(value)


def _table_hash_of(table: Mapping) -> int:
    return sum(hash_of(name) + hash_of(attr) for name, attr in table.items())


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


@partially
def like(
    imitating: Special[V],
    original: Special[V],
    *,
    _ids_of_found_values: Tuple[int] = tuple(),
) -> bool:
    """
    Predicate to compare two objects by value.
    An `imitating` object type must be covariant with an `original` object type.
    """

    return (
        imitating == original
        or hasattr(original, "__dict__")
        and isinstance(imitating, type(original))
        and id(imitating) not in _ids_of_found_values
        and id(original) not in _ids_of_found_values
        and (
            dict_of(original) == dict()
            or not set(dict_of(original).keys()) - set(dict_of(imitating).keys())
        )
        and all(
            like(
                dict_of(imitating)[attr_name],
                original_attr_value,
                _ids_of_found_values=(
                    *_ids_of_found_values, id(imitating), id(original)
                ),
            )
            for attr_name, original_attr_value in dict_of(original).items()
        )
    )


@partially
def to_attribute(
    attr_name: str,
    action: Callable[Optional[V], R],
    *,
    mutably: bool = False,
) -> LeftCallable[O, O]:
    """
    Function to calculate an attribute of an input object.

    Passes an input action a present attribute value (or `None` if it has no
    such attribute), sets the result to a clone (or the object itself depending
    on the `mutably` argument), and returns that object.
    """

    return mergely(
        (
            on(hasattr |by| attr_name, getattr |by| attr_name, else_=None)
            |then>> action
            |then>> (lambda value: returnly(lambda obj_: setattr(
                obj_, attr_name, value
            )))
        ),
        returned if mutably else copy,
    )
