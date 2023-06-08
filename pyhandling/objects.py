from functools import partial
from operator import attrgetter
from typing import (
    NoReturn, Mapping, Callable, Self, Generic, Concatenate, Any, Tuple
)

from pyannotating import Special

from pyhandling.annotations import K, V, event_for, Pm, R
from pyhandling.errors import InvalidInitializationError, UniaError
from pyhandling.partials import partially
from pyhandling.tools import action_repr_of


__all__ = (
    "NotInitializable",
    "Arbitrary",
    "dict_of",
    "of",
    "from_",
    "namespace_of",
    "void",
    "Unia",
)


class NotInitializable:
    """Mixin class preventing instantiation."""

    def __init__(self, *args, **kwargs) -> NoReturn:
        raise InvalidInitializationError(
            f"\"{type(self).__name__}\" type object cannot be initialized"
        )


class Arbitrary(Generic[Pm, R]):
    """
    Class for objects that do not have a common structure.
    To create with data use `of` constructor.
    """

    def __repr__(self) -> str:
        return "<{}>".format(', '.join(
            f"{name}={action_repr_of(value)}"
            for name, value in self.__dict__.items()
        ))

    def __and__(self, other: Special[Mapping]) -> Self:
        return of(**self.__dict__ | dict_of(other))

    def __eq__(self, other: Special[Mapping]) -> bool:
        return self.__dict__ == dict_of(other)


class _CallableArbitrary(Arbitrary):
    def __init__(self, action: Callable[Concatenate[Self, Pm] | Pm, R]):
        self.__action = action

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return (
            self.__action
            if isinstance(self.__action, staticmethod)
            else partial(self.__action, self)
        )(*args, **kwargs)


def dict_of(value: Special[Mapping[K, V]]) -> dict[K, V]:
    """
    Function converting an input value to `dict`.

    When passing a `Mapping` object, cast it to a `dict`, otherwise return
    `__dict__` of an input object.
    """

    return (
        dict(**value)
        if isinstance(value, Mapping) and not hasattr(value, "__dict__")
        else value.__dict__
    )


def of(get_object: event_for[V] = Arbitrary, /, **attributes) -> V:
    """
    Function to create an object with attributes from keyword arguments.
    Get object to modify from `get_object` parameter.

    When called on an `Arbitrary` object with a `__call__` attribute, makes it
    callable on that attribute as a method.
    """

    object_ = get_object()

    if isinstance(object_, Arbitrary) and "__call__" in attributes.keys():
        new_attributes = dict(attributes)
        del new_attributes["__call__"]

        return of(
            partial(_CallableArbitrary, attributes["__call__"]),
            **new_attributes
        )

    object_.__dict__ = dict_of(object_) | attributes

    return object_


@partially
def from_(parent: Special[Mapping], child: Special[Mapping]) -> Arbitrary:
    """
    Function for object-level inheritance.

    Summarizes data of input objects into an `Arbitrary` object. When passing a
    dictionary without `__dict__`, gets data from that dictionary.

    Child data is preferred over parent data.
    """

    return of(**dict_of(parent) | dict_of(child))


def namespace_of(object_: Special[Mapping]) -> Arbitrary:
    """
    Decorator for creating a namespace based on an input object.

    Creates an arbitrary object of an input object with `staticmethod` methods.
    Already `staticmethod` methods are not re-decorated.
    """

    return of(**{
        _: (
            staticmethod(value)
            if callable(value) and not isinstance(value, staticmethod)
            else value
        )
        for _, value in dict_of(object_).items()
    })


void = Arbitrary()  # Arbitrary object without data


class Unia:
    annotations = property(attrgetter("_annotations"))

    def __new__(cls, *annotations: Special[Self], **kwargs) -> Self:
        if len(annotations) == 1:
            return annotations[0]
        elif len(annotations) == 0:
            raise UniaError("Unia without annotations")
        else:
            return super().__new__(cls)

    def __init__(self, *annotations: Special[Self]) -> None:
        self._annotations = self._annotations_from(annotations)

    def __class_getitem__(cls, annotation_or_annotations: Special[tuple]) -> Self:
        return cls(*(
            annotation_or_annotations
            if isinstance(annotation_or_annotations, tuple)
            else (annotation_or_annotations, )
        ))

    def __instancecheck__(self, instance: Any) -> bool:
        return all(
            isinstance(instance, annotation) for annotation in self._annotations
        )

    @staticmethod
    def _annotations_from(annotations: Tuple[Special[Self]]) -> tuple:
        result_annotations = list()

        for annotation in annotations:
            if isinstance(annotation, Unia):
                result_annotations.extend(annotation.annotations)
            else:
                result_annotations.append(annotation)

        return tuple(result_annotations)
