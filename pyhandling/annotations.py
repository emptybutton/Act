from typing import Callable, Any

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation


dirty = FormalAnnotation(
    """
    Formal annotation to indicate the dirtyness of a function or any other
    callable object.
    """
)


handler_of = AnnotationTemplate(Callable, [[input_annotation], Any])

checker_of = AnnotationTemplate(Callable, [[input_annotation], bool])


factory_of = AnnotationTemplate(Callable, [..., input_annotation])


event_for = AnnotationTemplate(Callable,[[], input_annotation])


handler = handler_of[Any]

checker = checker_of[Any]


event = event_for[Any]
