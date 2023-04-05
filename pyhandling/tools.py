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
    "ArgumentKey",
    "ArgumentPack",
    "DelegatingProperty",
    "ActionWrapper",
    "contextual",
    "contextually",
    "context_oriented",
    "Clock",
    "Logger",
    "with_attributes",
    "as_argument_pack",
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


@dataclass(frozen=True)
class ArgumentKey(Generic[KeyT, ValueT]):
    """Data class for structuring getting value from `ArgumentPack` via `[]`."""

    key: KeyT
    is_keyword: bool = field(default=False, kw_only=True)
    default: ValueT | nothing = field(default_factory=lambda: nothing, compare=False, kw_only=True)


class ArgumentPack:
    """
    Data class for structuring the storage of any arguments.

    Has the ability to get an attribute when passed to `[]` `ArgumentKey`
    instance.
    """

    def __init__(self, args: Iterable = tuple(), kwargs: Optional[dict] = None):
        self._args = tuple(args)
        self._kwargs = MappingProxyType(kwargs if kwargs is not None else dict())

    @property
    def args(self) -> Tuple:
        return self._args

    @property
    def kwargs(self) -> MappingProxyType:
        return self._kwargs

    @cached_property
    def keys(self) -> Tuple[ArgumentKey, ...]:
        return (
            *map(ArgumentKey, range(len(self.args))),
            *map(partial(ArgumentKey, is_keyword=True), self.kwargs.keys())
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.__str__()})"

    def __str__(self) -> str:
        return "{formatted_args}{argument_separation_part}{formatted_kwargs}".format(
            formatted_args=', '.join(map(str, self.args)),
            argument_separation_part=', ' if self.args and self.kwargs else str(),
            formatted_kwargs=', '.join(map(lambda item: f"{item[0]}={item[1]}", self.kwargs.items())),
        )

    def __eq__(self, other: Special[Self]) -> bool:
        return (
            isinstance(other, ArgumentPack)
            and self.args == other.args
            and self.kwargs == other.kwargs
        )

    def __getitem__(self, argument: ArgumentKey) -> Any:
        return (
            (self.kwargs if argument.is_keyword else self.args)[argument.key]
            if argument in self or argument.default is nothing
            else argument.default
        )

    def __or__(self, other: Self) -> Self:
        return self.merge_with(other)

    def __contains__(self, argument: ArgumentKey) -> bool:
        return argument in self.keys

    def expand_with(self, *args, **kwargs) -> Self:
        """Method to create another pack with input arguments."""

        return self.__class__(
            (*self.args, *args),
            self.kwargs | kwargs
        )

    def merge_with(self, argument_pack: Self) -> Self:
        """Method to create another pack by merging with an input argument pack."""

        return self.__class__(
            (*self.args, *argument_pack.args),
            self.kwargs | argument_pack.kwargs
        )

    def only_with(self, *argument_keys: ArgumentKey) -> Self:
        """Method for cloning with values obtained from input keys."""

        keyword_argument_keys = set(filter(lambda argument_key: argument_key.is_keyword, argument_keys))

        return self.__class__(
            tuple(self[argument_key] for argument_key in set(argument_keys) - keyword_argument_keys),
            {keyword_argument_key.key: self[keyword_argument_key] for keyword_argument_key in keyword_argument_keys}
        )

    def without(self, *argument_keys: ArgumentKey) -> Self:
        """
        Method for cloning a pack excluding arguments whose keys are input to
        this method.
        """
        
        return self.only_with(*(set(self.keys) - set(argument_keys)))

    def call(self, caller: Callable) -> Any:
        """
        Method for calling an input function with arguments stored in an
        instance.
        """

        return caller(*self.args, **self.kwargs)

    @classmethod
    def of(cls, *args, **kwargs) -> Self:
        """Method for creating a pack with this method's input arguments."""

        return cls(args, kwargs)


class DelegatingProperty:
    """
    Descriptor class that takes data from an attribute that already exists in an
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

    def __init__(self, value: ValueT, when: ContextT = Type[nothing]):
        self._value = value
        self._context = when

    def __repr__(self) -> str:
        return f"{self.value} when {self.context}"

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))

    @classmethod
    def like(cls, value_and_context: tuple[ValueT, ContextT]) -> Self:
        """Class method to create from an unstructured collection."""

        value, context = value_and_context

        return cls(value, context)


class contextually(ActionWrapper, Generic[ActionT, ContextT]):
    action = DelegatingProperty("_action")
    context = DelegatingProperty("_context")

    def __init__(self, action: Callable[P, ResultT], when: ContextT = Type[nothing]):
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


def as_argument_pack(*args, **kwargs) -> ArgumentPack:
    """
    Function to optionally convert input arguments into `ArgumentPack` with
    that input arguments.

    When passed a single positional `ArgumentPack` to the function, it returns
    it.
    """

    if len(args) == 1 and isinstance(args[0], ArgumentPack) and not kwargs:
        return args[0]

    return ArgumentPack(args, kwargs)


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
