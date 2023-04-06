from abc import ABC, abstractmethod
from copy import deepcopy, copy
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps, cached_property, partial, update_wrapper
from inspect import Signature, signature, _empty
from math import inf
from types import MappingProxyType, MethodType
from typing import Callable, Self, Type, Any, runtime_checkable, Protocol, Generic, Final, Iterable, Optional, Tuple, _UnionGenericAlias, Union, NamedTuple, Iterator, Concatenate

from pyannotating import method_of, Special

from pyhandling.annotations import event_for, ObjectT, ValueT, KeyT, ResultT, ActionT, ContextT, one_value_action, dirty, reformer_of, P, TypeT
from pyhandling.errors import FlagError
from pyhandling.flags import nothing


__all__ = (
    "to_clone",
    "publicly_immutable",
    "property_of",
    "ActionWrapper",
    "contextual",
    "contextually",
    "ContextualError",
    "context_oriented",
    "Clock",
    "Logger",
    "with_attributes",
    "with_opened_items",
    "in_collection",
    "documenting_by",
)


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


class ActionWrapper(ABC, Generic[ActionT]):
    def __init__(self, action: ActionT):
        self._action = action
        self._become_native()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._action})"

    @property
    @abstractmethod
    def _force_signature(self) -> Signature:
        ...

    def _become_native(self) -> None:
        update_wrapper(self, self._action)
        self.__signature__ = self._force_signature


def calling_signature_of(action: Callable) -> Signature:
    try:
        return signature(action)
    except ValueError:
        return signature(lambda *args, **kwargs: ...)


def annotation_sum(*args: Special[_empty]) -> Any:
    annotations = tuple(arg for arg in args if arg is not _empty)

    return Union[*annotations] if annotations else _empty


class contextual(Generic[ValueT, ContextT]):
    """Representer of an input value as a value with a context."""

    value = DelegatingProperty("_value")
    context = DelegatingProperty("_context")

    def __init__(self, value: ValueT, when: ContextT = nothing):
        self._value = value
        self._context = when

    def __repr__(self) -> str:
        return f"{self.value} when {self.context}"

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))


class contextually(ActionWrapper, Generic[ActionT, ContextT]):
    action = DelegatingProperty("_action")
    context = DelegatingProperty("_context")

    def __init__(self, action: Callable[P, ResultT], when: ContextT = nothing):
        self._context = when
        super().__init__(action)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self._action(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.action} when {self.context}"

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))

    @property
    def _force_signature(self) -> Signature:
        return signature(self._action)


class ContextualError(Exception, Generic[ErrorT, ContextT]):
    """
    Error class to store the context of another error and itself.
    Iterates to unpack.
    """
   
    error = property_of("_ContextualError__error")
    context = property_of("_ContextualError__context")

    def __init__(self, error: ErrorT, context: ContextT):
        self.__error = error
        self.__context = context

        super().__init__(self._error_message)

    def __iter__(self) -> Iterator:
        return iter((self.__error, self.__context))
def context_oriented(root_values: tuple[ValueT, ContextT]) -> contextual[ContextT, ValueT]:
    """Function to swap a context and value."""

    context, value = root_values

    return contextual(value, when=context)


class Clock:
    """
    Atomic class for saving state.

    Has a number of ticks that determines its state.
    When ticks expire, it becomes `False` and may leave negative ticks.

    Keeps the original input ticks.
    """

    initial_ticks_to_disability = DelegatingProperty("_initial_ticks_to_disability")

    def __init__(self, ticks_to_disability: int):
        self.ticks_to_disability = self._initial_ticks_to_disability = ticks_to_disability

    def __repr__(self) -> str:
        return f"{'in' if not self else str()}valid {self.__class__.__name__}({self.ticks_to_disability})"

    def __bool__(self) -> bool:
        return self.ticks_to_disability > 0


class Logger:
    """
    Class for logging any messages.

    Stores messages via the input value of its call.

    Has the ability to clear logs when their limit is reached, controlled by the
    `maximum_log_count` attribute and the keyword argument.

    Able to save the date of logging in the logs. Controlled by `is_date_logging`
    attribute and keyword argument.
    """

    def __init__(
        self,
        logs: Iterable[str] = tuple(),
        *,
        maximum_log_count: int | float = inf,
        is_date_logging: bool = False
    ):
        self._logs = list()
        self.maximum_log_count = maximum_log_count
        self.is_date_logging = is_date_logging

        for log in logs:
            self(log)

    @property
    def logs(self) -> Tuple[str, ...]:
        return tuple(self._logs)

    def __call__(self, message: str) -> None:
        self._logs.append(
            message
            if not self.is_date_logging
            else f"[{datetime.now()}] {message}"
        )

        if len(self._logs) > self.maximum_log_count:
            self._logs = self._logs[self.maximum_log_count:]


def with_attributes(
    get_object: event_for[ObjectT] = type(
        "_with_attributes__default_object_type",
        tuple(),
        {'__doc__': (
            """
            Class used as a standard object factory for subsequent stuffing with
            attributes in `with_attributes`
            """
        )}
    ),
    **attributes,
) -> ObjectT:
    """
    Function to create an object with attributes from keyword arguments.
    Sets attributes manually.
    """

    attribute_keeper = get_object()
    attribute_keeper.__dict__ = attributes

    return attribute_keeper


def with_opened_items(collection: Iterable) -> Tuple:
    """Function to expand input collection's subcollections to it."""

    collection_with_opened_items = list()

    for item in collection:
        if not isinstance(item, Iterable):
            collection_with_opened_items.append(item)
            continue

        collection_with_opened_items.extend(item)

    return tuple(collection_with_opened_items)


def in_collection(value: ValueT) -> tuple[ValueT]:
    """Function to represent the input value as a single collection."""

    return (value, )


def documenting_by(documentation: str) -> dirty[reformer_of[ObjectT]]:
    """
    Function of getting other function that getting value with the input 
    documentation from this first function.
    """

    def document(object_: ObjectT) -> ObjectT:
        """
        Function created with `documenting_by` function that sets the __doc__
        attribute and returns the input object.
        """

        object_.__doc__ = documentation
        return object_

    return document
