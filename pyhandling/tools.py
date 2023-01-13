from copy import copy
from dataclasses import dataclass, field
from functools import wraps, cached_property, partial
from math import inf
from typing import Callable, Self, Iterable


def to_clone(method: Callable[[object, ...], None]) -> Callable[[...], object]:
    """
    Decorator function to spawn new objects by cloning and applying an input
    method to them.
    """

    @wraps(method)
    def wrapper(instance: object, *args, **kwargs) -> object:
        clone = copy(instance)
        method(clone, *args, **kwargs)

        return clone

    wrapper.__annotations__['return'] = Self

    return wrapper


@dataclass(frozen=True)
class ArgumentKey:
    """Data class for structuring getting value from ArgumentPack via []."""

    key: any
    is_keyword: bool = field(default=False, kw_only=True)


@dataclass(frozen=True)
class ArgumentPack:
    """
    Data class for structuring the storage of any arguments.

    Has the ability to get an attribute when passed to [] an ArgumentKey
    instance.
    """

    args: Iterable = tuple()
    kwargs: dict = field(default_factory=dict)

    @cached_property
    def keys(self) -> tuple[ArgumentKey]:
        return (
            *map(ArgumentKey, range(len(self.args))),
            *map(partial(ArgumentKey, is_keyword=True), self.kwargs.keys())
        )

    def __getitem__(self, argument: ArgumentKey) -> any:
        return (self.kwargs if argument.is_keyword else self.args)[argument.key]

    def __or__(self, other: Self) -> Self:
        return self.merge_with(other)

    def __contains__(self, argument: ArgumentKey) -> bool:
        return argument.key in (self.kwargs.keys() if argument.is_keyword else self.args)

    def expand_with(self, *args, **kwargs) -> None:
        """Method to create another pack with input arguments."""

        return self.__class__(
            (*self.args, *args),
            self.kwargs | kwargs
        )

    def merge_with(self, argument_pack: Self) -> None:
        """Method to create another pack by merging with an input argument pack."""

        return self.__class__(
            (*self.args, *argument_pack.args),
            self.kwargs | argument_pack.kwargs
        )

    def only_with(self, *argument_keys: ArgumentKey) -> Self:
        """Method for cloning with values obtained from input keys."""

        keyword_argument_keys = set(filter(lambda argument_key: argument_key.is_keyword, argument_keys))

        return self.__class__(
            tuple(self[argument_key] for argument_key in set(arguments) - keyword_argument_keys),
            {keyword_argument_key.key: self[keyword_argument_key] for keyword_argument_key in keyword_argument_keys}
        )

    def without(self, *arguments: ArgumentKey) -> Self:
        """
        Method for cloning a pack excluding arguments whose keys are input to
        this method.
        """
        
        return self.only_with(*(set(self.keys) - set(arguments)))

    def call(self, caller: Callable) -> any:
        """
        Method for calling an input function with arguments stored in an
        instance.
        """

        return caller(*self.args, **self.kwargs)

    @classmethod
    def create_via_call(cls, *args, **kwargs) -> Self:
        """Method for creating a pack with this method's input arguments."""

        return cls(args, kwargs)


class DelegatingProperty:
    """
    Descriptor class that takes data from an attribute that already exists on an
    object.

    Has the ability to set a delegating attribute (but it's better not to do so).
    """

    def __init__(
        self,
        delegated_attribute_name: str,
        *,
        settable: bool = False,
        geting_value_converter: Callable[[any], any] = lambda resource: resource,
        seting_value_converter: Callable[[any], any] = lambda resource: resource
    ):
        self.delegated_attribute_name = delegated_attribute_name
        self.settable = settable
        self.geting_value_converter = geting_value_converter
        self.seting_value_converter = seting_value_converter

    def __get__(self, instance: object, owner: type) -> any:
        return self.geting_value_converter(getattr(instance, self.delegated_attribute_name))

    def __set__(self, instance: object, value: any) -> None:
        if not self.settable:
            raise AttributeError(
                "delegating property of '{attribute_name}' for '{class_name}' object is not settable".format(
                    attribute_name=self.delegated_attribute_name,
                    class_name=type(instance).__name__
                )
            )

        setattr(instance, self.delegated_attribute_name, self.seting_value_converter(value))


class Clock:
    """
    Atomic class for saving state.

    Has a number of ticks that determines its state.
    When ticks expire, it becomes "False" and may leave negative ticks.

    The client himself determines the state of anything by the clock, so he can
    move ticks as he pleases.

    Keeps the original input ticks.
    """

    initial_ticks_to_disability = DelegatingProperty('_initial_ticks_to_disability')

    def __init__(self, ticks_to_disability: int):
        self.ticks_to_disability = self._initial_ticks_to_disability = ticks_to_disability

    def __repr__(self) -> str:
        return f"{'in' if not self else str()}valid {self.__class__.__name__}({self.ticks_to_disability})"

    def __bool__(self) -> bool:
        return self.ticks_to_disability > 0


def get_collection_from(*collections: Iterable) -> tuple:
    """Function to get a collection with elements from input collections."""

    return get_collection_with_reduced_nesting(collections, 1)


def get_collection_with_reduced_nesting(collection: Iterable, number_of_reductions: int = inf) -> tuple:
    """Function that allows to get a collection with a reduced nesting level."""

    reduced_collection = list()

    for item in collection:
        if not isinstance(item, Iterable):
            reduced_collection.append(item)
            continue

        reduced_collection.extend(
            get_collection_with_reduced_nesting(item, number_of_reductions - 1)
            if number_of_reductions > 1
            else item
        )

    return tuple(reduced_collection)


def as_argument_pack(*args, **kwargs) -> ArgumentPack:
    """
    Function to optionally convert input arguments into an ArgumentPack with
    that input arguments.

    When passed a single positional ArgumentPack to the function, it returns it.
    """

    if len(args) == 1 and isinstance(args[0], ArgumentPack) and not kwargs:
        return args[0]

    return ArgumentPack(args, kwargs)
