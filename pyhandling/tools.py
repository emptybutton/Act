from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Self, Iterable, Union, Mapping, Final


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


class AnnotationFactory(ABC):
    """
    Annotation factory class.
    Creates annotation by input other.

    Can be used via [] (preferred) or by normal call.
    """

    def __call__(self, annotation: any) -> any:
        return self._create_full_annotation_by(annotation)

    def __getitem__(self, annotation: any) -> any:
        return self._create_full_annotation_by(
            Union[annotation]
            if isinstance(annotation, Iterable)
            else annotation
        )

    @abstractmethod
    def _create_full_annotation_by(self, annotation: any) -> any:
        """Annotation Creation Method from an input annotation."""


class CustomAnnotationFactory(AnnotationFactory):
    """
    AnnotationFactory class delegating the construction of another factory's
    annotation.

    When called, replaces the 'annotation' strings from its arguments and their
    subcollections with the input annotation.
    """

    _input_annotation_annotation: any = '<input_annotation>'

    input_annotation_annotation = classmethod(DelegatingProperty(
        '_input_annotation_annotation'
    ))

    original_factory = DelegatingProperty('_original_factory')
    annotations = DelegatingProperty('_annotations')

    def __init__(self, original_factory: Mapping, annotations: Iterable):
        self._original_factory = original_factory
        self._annotations = tuple(annotations)

    def __repr__(self) -> str:
        return "{factory}{arguments}".format(
            factory=(
                self._original_factory.__name__
                if hasattr(self._original_factory, '__name__')
                else self._original_factory
            ),
            arguments=list(self._annotations)
        )

    def _create_full_annotation_by(self, annotation: any) -> any:
        return self._original_factory[
            *self.__get_formatted_annotations_from(self._annotations, annotation)
        ]

    def __get_formatted_annotations_from(self, annotations: Iterable, replacement_annotation: any) -> tuple:
        """
        Recursive function to replace element(s) of the input collection (and
        its subcollections) equal to 'annotation' with the input annotation.
        """

        formatted_annotations = list()

        for annotation in annotations:
            if annotation == self._input_annotation_annotation:
                annotation = replacement_annotation
            elif isinstance(annotation, Iterable) and not isinstance(annotation, str):
                annotation = self.__get_formatted_annotations_from(
                    annotation,
                    replacement_annotation
                )

            formatted_annotations.append(annotation)

        return tuple(formatted_annotations)


CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE: Final = (
    """
    CustomAnnotationFactory instance.
    {}
    See AnnotationFactory for more info.
    """
)


handler_of = CustomAnnotationFactory(
    Callable,
    [[CustomAnnotationFactory.input_annotation_annotation], any]
)
handler_of.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes one parameter (the type of which
    this factory accepts) and returns whatever it wants.
    """
)


checker_of = CustomAnnotationFactory(
    Callable,
    [[CustomAnnotationFactory.input_annotation_annotation], bool]
)
checker_of.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes one parameter (the type of which
    this factory accepts) and returns the result of the check (bool).
    """
)


factory_of = CustomAnnotationFactory(
    Callable,
    [..., CustomAnnotationFactory.input_annotation_annotation]
)
factory_of.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes any parameters and returns the type
    of which this factory accepts.
    """


event_for = CustomAnnotationFactory(
    Callable,
    [[], CustomAnnotationFactory.input_annotation_annotation]
)
event_for.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes no parameters and returns the type
    of which this factory accepts.
    """
)


Handler = handler_of[any]
Handler.__doc__ = (
    """
    Annotation of non-strict handler of something.
    Created by handler_of and equivalently handler_of[any].
    """
)


)