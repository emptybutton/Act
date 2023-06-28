from copy import copy
from functools import reduce
from operator import or_
from types import MethodType
from typing import (
    Mapping, Callable, Self, Generic, Concatenate, Any, Optional, ClassVar,
    Tuple
)

from pyannotating import Special

from act.annotations import K, V, Pm, R, O
from act.contexting import (
    contextually, contexted, contextualizing, as_
)
from act.data_flow import mergely, by, returnly
from act.errors import ObjectTemplateError
from act.flags import flag_about, Flag
from act.immutability import to_clone
from act.partiality import partially, flipped
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
    "of",
    "void",
    "like",
    "to_attribute",
)


as_method = contextualizing(flag_about("as_method"), to=contextually)


class obj:
    """
    Constructor for objects that do not have a common structure.

    Creates an object with attributes from keyword arguments.

    When called with a `__call__` attribute, makes an output object callable on
    that attribute as a method.

    Can be obtained union of an instance with any other object via `&`.
    """

    _to_fill: ClassVar[Flag] = contextualizing(flag_about("to_fill"))

    def __new__(
        cls,
        *,
        __call__: Optional[Callable[Concatenate[Self, Pm], R]] = None,
        **attributes: Special[as_method[Callable[[Self, Any], Any]] | _to_fill[Any]],
    ) -> "Special[_callable_obj[Pm, R] | temp, Self]":
        if cls is not temp and any(
            contexted(attr) == obj._to_fill for attr in attributes.values()
        ):
            return temp(__call__=__call__, **attributes)

        return (
            _callable_obj(__call__=__call__, **attributes)
            if __call__ is not None and cls is obj
            else super().__new__(cls)
        )

    def __init__(self, **attributes: Special[as_method[Callable[Self, Any]]]):
        self.__dict__ = attributes

    def __repr__(self) -> str:
        return "<{}>".format(', '.join(
            f"{name}{self._field_repr_of('<...>' if value is self else value)}"
            for name, value in self.__dict__.items()
        ))

    def __getattribute__(self, attr_name: str) -> Any:
        value = object.__getattribute__(self, attr_name)
        action, context = contexted(value)

        return MethodType(action, self) if context == as_method else value

    @staticmethod
    def __repr_of(value: Any) -> str:
        try:
            return code_like_repr_of(value)
        except RecursionError:
            return '...'

    def __eq__(self, other: Special[Self]) -> bool:
        return dict_of(self) == dict_of(other)

    def __and__(self, other: Special[Mapping]) -> Self:
        return self.__summing_by(other)(self, other)

    def __rand__(self, other: Special[Mapping]) -> Self:
        return self.__summing_by(other)(other, self)

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

    def _field_repr_of(self, value: Any) -> str:
        return f"={code_like_repr_of(value)}"

    @classmethod
    def __summing_by(cls, value: Special["temp"]) -> Callable[..., Self]:
        return (temp if cls is temp or type(value) is temp else obj).of


class _callable_obj(obj, LeftCallable, Generic[Pm, R]):
    """Variation of `obj` for callability."""

    def __init__(
        self,
        *,
        __call__: Callable[Concatenate[Self, Pm], R], **attributes,
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


class temp(obj, LeftCallable):
    _filled: ClassVar[Flag] = contextualizing(flag_about("filled"))

    def __init__(self, **attributes: Special[_filled[Any]]):
        super().__init__(**{
            _: (
                value
                if contexted(value).context == temp._filled
                else as_(obj._to_fill, value)
            )
            for _, value in attributes.items()
        })

    def __repr__(self) -> str:
        return super().__repr__() if dict_of(self) else f"{type(self).__name__}()"

    def __call__(self, *attrs, **kwattrs) -> obj:
        names_to_fill = tuple(
            name
            for name, value in self.__dict__.items()
            if value.context == obj._to_fill
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
        return len(set(dict_of(self).keys()) - set(dict_of(instance).keys())) == 0

    @classmethod
    def of(cls, *objects: Special[Mapping]) -> Self:
        return cls(**{
            _: (
                value
                if contexted(value).context == obj._to_fill
                else as_(temp._filled, value)
            )
            for _, value in reduce(or_, map(dict_of, objects)).items()
        })

    def _field_repr_of(self, value: Any) -> str:
        stored_value, context = contexted(value)

        if context is obj._to_fill:
            return f": {code_like_repr_of(stored_value)}"
        elif context == temp._filled:
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
