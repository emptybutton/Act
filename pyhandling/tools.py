from copy import copy
from dataclasses import dataclass, field
from functools import wraps
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

    def __getitem__(self, argument: ArgumentKey) -> any:
        return (self.kwargs if argument.is_keyword else self.args)[argument.key]

    @to_clone
    def expand_with(self, *args, **kwargs) -> Self:
        """Method to create another pack with input arguments."""

        self.args = (*self.args, *args)
        self.kwargs = self.kwargs | kwargs

    @to_clone
    def merge_with(self, argument_pack: Self) -> Self:
        """Method to create another pack by merging with an input argument pack."""

        self.args = (*self.args, *argument_pack.args)
        self.kwargs = self.kwargs | argument_pack.kwargs

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

