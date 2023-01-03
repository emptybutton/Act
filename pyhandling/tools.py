from copy import copy
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Iterable, Self, Union, _CallableGenericAlias


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
class ArgumentPack:
    """Data class for structuring arguments."""

    args: Iterable = tuple()
    kwargs: dict = field(default_factory=dict)

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
        value_converter: Callable[[any], any] = lambda resource: resource
    ):
        self.delegated_attribute_name = delegated_attribute_name
        self.settable = settable
        self.value_converter = value_converter

    def __get__(self, instance: object, owner: type) -> any:
        return getattr(instance, self.delegated_attribute_name)

    def __set__(self, instance: object, value: any) -> None:
        if not self.settable:
            raise AttributeError(
                "delegating property of '{attribute_name}' for '{class_name}' object is not settable".format(
                    attribute_name=self.delegated_attribute_name,
                    class_name=type(instance).__name__
                )
            )

        setattr(instance, self.delegated_attribute_name, self.value_converter(value))


class Clock:
    """
    Atomic class for saving state.

    Has a number of ticks that determines its state.
    When ticks expire, it becomes "False" and may leave negative ticks.

    The client himself determines the state of anything by the clock, so he can
    move ticks as he pleases.

    """


    def __init__(self, ticks_to_disability: int):
        self._ticks_to_disability = ticks_to_disability

    def __repr__(self) -> str:
        return f"{'in' if not self else str()}valid {self.__class__.__name__}({self.ticks_to_disability})"

    def __bool__(self) -> bool:
        return self.ticks_to_disability > 0


class HandlerAnnotationFactory:
    """
    Callable annotation factory class.

    Creates a Callable annotation that takes one parameter (the type of which
    this factory accepts) and returns whatever it wants.

    Can be used via [] (preferred) or by normal call.
    """

    def __call__(self, handler_input_annotation: any) -> _CallableGenericAlias:
        return self._create_handler_annotation_by(handler_input_annotation)

    def __getitem__(self, handler_input_annotation: any) -> _CallableGenericAlias:
        return self._create_handler_annotation_by(handler_input_annotation)

    def _create_handler_annotation_by(self, handler_input_annotation: any) -> _CallableGenericAlias:
        """Annotation Creation Method."""

        return Callable[
            [
                Union[handler_input_annotation]
                if isinstance(handler_input_annotation, Iterable)
                else handler_input_annotation
            ],
            any
        ]


handler_of = HandlerAnnotationFactory()
handler_of.__doc__ = (
    """
    Standard HandlerAnnotationFactory instance for quick access to its benefits.
    See it for more info.
    """
)