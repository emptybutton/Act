from abc import ABC, abstractmethod
from collections import OrderedDict
from copy import copy, deepcopy
from dataclasses import dataclass, MISSING
from functools import reduce
from operator import or_, attrgetter, methodcaller
from types import MethodType
from typing import (
    Mapping, Callable, Self, Generic, Concatenate, Any, Optional, Tuple, ClassVar,
    Iterable
)

from pyannotating import Special

from act.aggregates import Access
from act.annotations import K, V, Pm, R, O, Union, CommentAnnotation
from act.atomization import fun
from act.contexting import (
    contextually, contexted, contextualizing, be
)
from act.data_flow import (
    mergely, by, io, when, eventually, and_via_indexer, indexer_of
)
from act.errors import ObjectTemplateError
from act.error_flow import raising
from act.flags import flag_about
from act.immutability import to_clone
from act.partiality import partially, flipped, partial
from act.pipeline import then, _generating_pipeline
from act.representations import code_like_repr_of
from act.synonyms import on
from act.signatures import call_signature_of
from act.tools import documenting_by, _get


__all__ = (
    "as_method",
    "as_descriptor",
    "as_property",
    "Arbitrary",
    "with_default_descriptor",
    "default_descriptor",
    "obj",
    "temp",
    "is_templated",
    "templated_attrs_of",
    "dict_of",
    "hash_of",
    "expand",
    "from_",
    "like",
    "to_attr",
    "read_only",
    "sculpture_of",
    "original_of",
    "out",
)


as_method = contextualizing(flag_about("as_method"), to=contextually)
as_descriptor = contextualizing(flag_about("as_descriptor"))


def as_property(
    maybe_property: Callable['obj', R] | property,
    setter: Optional[Callable[['obj', Any], Any]] = None,
    deleter: Optional[Callable['obj', Any]] = None,
) -> as_descriptor[Callable['obj', R] | property]:
    property_ = (
        maybe_property
        if isinstance(maybe_property, property)
        else property(maybe_property)
    )

    if setter is not None:
        property_ = property_.setter(setter)

    if deleter is not None:
        property_ = property_.deleter(deleter)

    return as_descriptor(property_)


class Arbitrary(ABC):
    """
    Interface for objects that do not have a common structure.

    To create an arbitrary object with data, use the `obj` constructor.

    To create an object annotated with data and its future filling, use the
    `temp` constructor.

    Data from any several objects can be combined using the `&` operator from
    an arbitrary object or `of` classmethod of one of the constructors.

    `Arbitrary` objects are compared only by value without type qualification.

    For covariant value checking use the `isinstance` function.
    `|` supported for `Union`.


    When called with a `__call__` attribute, makes an output object callable on
    that attribute.

    Can be obtained union of an instance with any other object via `&`.
    """

    @abstractmethod
    def __init__(self, **attributes):
        ...

    @abstractmethod
    def __hash__(self) -> int:
        ...

    @abstractmethod
    def __add__(self, attr_name: str) -> Self:
        ...

    @abstractmethod
    def __sub__(self, attr_name: str) -> Self:
        ...

    @abstractmethod
    def __and__(self, other: Any) -> Self:
        ...

    @abstractmethod
    def __rand__(self, other: Any) -> Self:
        ...

    @abstractmethod
    def __or__(self, other: Any) -> Any:
        ...

    @abstractmethod
    def __ror__(self, other: Any) -> Any:
        ...

    @classmethod
    @abstractmethod
    def of(cls, *objects: Special[Mapping]) -> Self:
        """
        Constructor for data from other objects.
        Data of subsequent objects have higher priority than previous ones.
        """


class _AttributeKeeper(Arbitrary, ABC):
    _ignored_attribute_names: ClassVar[Tuple[str]] = (
        "__dict__", "__weakref__", "__slots__"
    )

    def __init__(self, **attributes):
        self.__dict__ = {
            name: type(self)._for_setting(attr)
            for name, attr in attributes.items()
            if name not in type(self)._ignored_attribute_names
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

    def __copy__(self) -> Self:
        return type(self)(**dict_of(self))

    def __eq__(self, other: Special[Self]) -> bool:
        return dict_of(self) == dict_of(other)

    @to_clone
    def __add__(self, attr_name: str) -> Self:
        if not hasattr(self, attr_name):
            setattr(self, attr_name, None)

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
        return cls(**reduce(or_, map(dict_of, objects)))


@partially
def with_default_descriptor(
    descriptor_of: Callable[str, Any],
    obj_: Arbitrary,
) -> Arbitrary:
    obj_ = copy(obj_)
    setattr(obj_, default_descriptor, descriptor_of)
    return obj_


default_descriptor: str = "_obj_default_descriptor_of__"


def default_descriptor_of(obj: Any) -> Special[None]:
    return (
        getattr(obj, default_descriptor)
        if hasattr(obj, default_descriptor)
        else None
    )


_to_fill = contextualizing(flag_about("_to_fill"))
_filled = contextualizing(flag_about("_filled"))

_of_temp = _to_fill | _filled

_NO_VALUE = flag_about("_NO_VALUE")


class obj(_AttributeKeeper):
    """Constructor for an `Arbitrary` object with data."""

    def __new__(
        cls,
        *,
        __call__: Callable[Concatenate[Self, Pm], R] | _NO_VALUE = _NO_VALUE,
        **attributes: Any,
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

    def __getitem__(self, item: Special[tuple]) -> CommentAnnotation:
        return CommentAnnotation("obj(...)")[item]

    def __getattribute__(self, attr_name: str) -> Any:
        if attr_name == "__dict__":
            return object.__getattribute__(self, attr_name)

        if (
            attr_name not in self.__dict__.keys()
            and default_descriptor in self.__dict__.keys()
        ):
            default_descriptor_ = default_descriptor_of(self)(attr_name)
            if hasattr(default_descriptor_, "__get__"):
                return default_descriptor_.__get__(self, type(self))

        value = object.__getattribute__(self, attr_name)
        context, stored_value = contexted(value)

        if context == as_method:
            return MethodType(stored_value, self)
        elif context == as_descriptor:
            return (
                stored_value.__get__(self, type(self))
                if hasattr(stored_value, "__get__")
                else stored_value
            )
        else:
            return value

    def __setattr__(self, attr_name: str, value: Any) -> Any:
        if attr_name == "__dict__":
            return super().__setattr__(attr_name, value)

        if attr_name not in self.__dict__.keys():
            if default_descriptor in self.__dict__.keys():
                default_descriptor_ = default_descriptor_of(self)(attr_name)
                if hasattr(default_descriptor_, "__set__"):
                    return default_descriptor_.__set__(self, value)
            else:
                return super().__setattr__(attr_name, value)

        context, setter = contexted(self.__dict__[attr_name])

        return (
            setter.__set__(self, value)
            if context == as_descriptor and hasattr(setter, "__set__")
            else super().__setattr__(attr_name, value)
        )

    def __delattr__(self, attr_name: str) -> Any:
        if attr_name == "__dict__":
            return super().__delattr__(attr_name)

        if attr_name not in self.__dict__.keys():
            if default_descriptor_ in self.__dict__.keys():
                default_descriptor_ = default_descriptor_of(self)
                if hasattr(default_descriptor_, "__delete__"):
                    return default_descriptor_of(self).__delete__(self)
            else:
                return super().__delattr__(attr_name)

        context, deleter = contexted(self.__dict__[attr_name])

        return (
            deleter.__delete__(self)
            if context == as_descriptor and hasattr(deleter, "__delete__")
            else super().__delattr__(attr_name)
        )

    def __instancecheck__(self, instance: Any) -> bool:
        return all(
            hasattr(instance, name) and getattr(instance, name) == attr
            for name, attr in dict_of(self).items()
        )

    @staticmethod
    @partially
    def to_attr(
        attr_name: str,
        action: Callable[Optional[V], R],
        *,
        mutably: bool = False,
    ) -> Callable[O, Self]:
        return fun(obj.of |then>> to_attr(attr_name, action, mutably=mutably))

    @staticmethod
    def _for_setting(value: V) -> V:
        return value

    @staticmethod
    def _field_repr_of(value: Any) -> str:
        return f"={code_like_repr_of(value)}"


class _callable_obj(obj, Generic[Pm, R]):
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

    __or__ = _generating_pipeline(obj.__or__)


class temp(_AttributeKeeper):
    """Constructor for an `Arbitrary` object without data."""

    def __new__(cls, **attributes: Any) -> Self | obj:
        return (
            obj(**attributes)
            if all(
                contexted(attr).context == _filled
                for attr in attributes.values()
            )
            else super().__new__(cls)
        )

    def __repr__(self) -> str:
        return super().__repr__() if dict_of(self) else f"{type(self).__name__}()"

    def __deepcopy__(self, memo) -> Self:
        return temp(**{
            _: attr.context(deepcopy(attr.value, memo))
            for _, attr in dict_of(self).items()
        })

    def __getitem__(self, item: Special[tuple]) -> CommentAnnotation:
        return CommentAnnotation("temp(...)")[item]

    def __getattribute__(self, name: str) -> Any:
        attr = object.__getattribute__(self, name)

        if contexted(attr).context == _filled:
            return attr.value
        elif contexted(attr).context == _to_fill:
            raise ObjectTemplateError("getting a template attribute")
        else:
            return attr

    def __setattr__(self, name: str, value: Any) -> None:
        partial(super().__setattr__, name)(
            value if name == "__dict__" else temp._unit_of(value)
        )

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
            else be(_filled, value)
        )

    @staticmethod
    def _for_setting(value: V) -> _filled[V] | _to_fill[V]:
        return (
            value
            if contexted(value).context == _filled
            else be(_to_fill, value)
        )

    @staticmethod
    def _field_repr_of(value: Any) -> str:
        context, stored_value = contexted(value)

        if context is _to_fill:
            return f": {code_like_repr_of(stored_value)}"
        elif context == _filled:
            return f"={code_like_repr_of(stored_value)}"
        elif context == as_method:
            return f"()={code_like_repr_of(stored_value)}"
        else:
            return f"={code_like_repr_of(value)}"


def struct(type_: type) -> temp:
    dataclass_ = dataclass(type_)

    return temp(**{
        field.name: field >= when(
            (
                lambda f: f.default is not MISSING,
                attrgetter("default") |then>> _filled,
            ),
            (
                lambda f: f.default_factory is not MISSING,
                methodcaller("default_factory") |then>> _filled,
            ),
            (..., attrgetter("type")),
        )
        for field in dict_of(dataclass_)["__dataclass_fields__"].values()
    })


def name_enum_of(annotated: temp(__annotations__=Iterable[str])) -> obj:
    return obj.of({name: name for name in annotated.__annotations__.keys()})


@partially
def is_templated(attr_name: str, obj_: Special[temp]) -> bool:
    return (
        attr_name in dict_of(obj_).keys()
        and contexted(dict_of(obj_)[attr_name]).context == _to_fill
    )


def templated_attrs_of(obj_: Special[temp]) -> OrderedDict[str, Any]:
    return OrderedDict(
        (name, attr.value)
        for name, attr in dict_of(obj_).items()
        if contexted(attr).context == _to_fill
    )


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
@to_clone
def expand(object_: O, data: Special[Mapping], /) -> O:
    """
    Function to set all attributes of a second input object to a clone of a
    first input object.
    """

    object_.__dict__ = dict_of(object_) | dict_of(data)


from_ = partially(flipped(expand))


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
def to_attr(
    attr_name: str,
    action: Callable[Optional[V], R],
    *,
    mutably: bool = False,
) -> Callable[O, O]:
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
            |then>> (lambda value: io(lambda obj_: setattr(
                obj_, attr_name, value
            )))
        ),
        _get if mutably else copy,
    )


@and_via_indexer(indexer_of(CommentAnnotation("read_only")))
def read_only(value: Special[str | Callable | Access]) -> property:
    """Function declaring a readonly descriptor."""

    raise_error = raising(AttributeError("attribute cannot be set"))

    if isinstance(value, Access):
        return read_only(value.get)
    elif isinstance(value, property):
        return property(value.fget, raise_error, value.fdel)
    elif isinstance(value, str):
        return property(attrgetter(value), raise_error)
    elif callable(value):
        return property(value, raise_error)
    else:
        return property(lambda v: value.__get__(v, type(v)))


@partially
def sculpture_of(
    original: Any,
    **descriptor_by_attr_name: Special[str | Callable | Access],
) -> obj:
    """Constructor for objects with proxied descriptors to an input value."""

    return (
        obj.of({
            _: as_descriptor(_sculpture_property_of(
                _as_sculpture_descriptor(descriptor),
                original,
            ))
            for _, descriptor in descriptor_by_attr_name.items()
        })
        & obj(_sculpture_original=original)
    )


original_of: Callable[Any, Any]
original_of = documenting_by(
    """Function for a value to which an input sculpture proxies."""
)(
    fun(attrgetter("_sculpture_original"))
)


class out:
    """Decorator for optional attribute operations."""

    def __init__(self, value: Any):
        self.__value = value

    def __repr__(self) -> str:
        return f"out({code_like_repr_of(self.__value)})"

    def __getattr__(self, attr_name: str) -> Any:
        return (
            getattr(self.__value, attr_name)
            if hasattr(self.__value, attr_name)
            else None
        )

    def __setattr__(self, attr_name: str, value: Any) -> Any:
        if attr_name == "_out__value":
            return super().__setattr__(attr_name, value)

        if not hasattr(self.__value, attr_name):
            return None

        setattr(self.__value, attr_name, value)
        return self.__value

    def __delattr__(self, attr_name: str) -> Any:
        if not hasattr(self.__value, attr_name):
            return None

        delattr(self.__value, attr_name)
        return self.__value


def _as_sculpture_descriptor(
    value: Union[
        str,
        Callable[Any, Any],
        Access[Callable[Any, Any], Callable[[Any, Any], Any]],
        V,
    ]
) -> property | V:
    if isinstance(value, str):
        return property(attrgetter(value), lambda o, v: setattr(o, value, v))
    elif isinstance(value, Access):
        return property(value.get, value.set)
    elif callable(value):
        return property(value)
    else:
        return value


def _sculpture_property_of(descriptor: Any, value: Any) -> property:
    sculpture_property = property()

    if hasattr(descriptor, "__set__"):
        sculpture_property = property(
            fset=lambda _, v: descriptor.__set__(value, v),
        )

    if hasattr(descriptor, "__get__"):
        sculpture_property = property(
            eventually(descriptor.__get__, value, type(value)),
            sculpture_property.fset,
        )

    if hasattr(descriptor, "__delete__"):
        sculpture_property = property(
            sculpture_property.fget,
            sculpture_property.fset,
            eventually(descriptor.__delete__, value),
        )

    return sculpture_property
