from copy import copy
from typing import Any, Final, Callable

from pyannotating import FormalAnnotation, CustomAnnotationFactory, input_annotation


dirty = FormalAnnotation(
    """
    Formal annotation to indicate the dirtyness of a function or any other
    callable object.
    """
)


CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE: Final[str] = (
    """
    CustomAnnotationFactory instance.
    {}
    See AnnotationFactory for more info.
    """
)


handler_of = CustomAnnotationFactory(Callable, [[input_annotation], Any])
handler_of.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes one parameter (the type of which
    this factory accepts) and returns whatever it wants.
    """
)


checker_of = CustomAnnotationFactory(Callable, [[input_annotation], bool])
checker_of.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes one parameter (the type of which
    this factory accepts) and returns the result of the check (bool).
    """
)


factory_of = CustomAnnotationFactory(Callable, [..., input_annotation])
factory_of.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes any parameters and returns the type
    of which this factory accepts.
    """
)


event_for = CustomAnnotationFactory(Callable,[[], input_annotation])
event_for.__doc__ = CUSTOM_ANNOTATION_FACTORY_INSTANCE_DOCUMENTATION_TEMPLATE.format(
    """
    Creates a Callable annotation that takes no parameters and returns the type
    of which this factory accepts.
    """
)


Handler = handler_of[Any]
Handler.__doc__ = (
    """
    Annotation of non-strict handler of something.
    Created by handler_of and equivalently handler_of[Any].
    """
)


Checker = checker_of[Any]
Checker.__doc__ = (
    """
    Annotation of non-strict checker of something.
    Created by checker_of and equivalently checker_of[Any].
    """
)


Event = event_for[Any]
Event.__doc__ = (
    """
    Event annotation, non-strict on the return type.
    Created by event_for and equivalently event_for[Any].
    """
)