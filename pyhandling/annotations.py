from typing import Callable, Any, Self

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation


dirty = FormalAnnotation(
    """
    Formal annotation to indicate the dirtyness of a function or any other
    callable object.
    """
)


handler_of = AnnotationTemplate(Callable, [[input_annotation], Any])

checker_of = AnnotationTemplate(Callable, [[input_annotation], bool])

formatter_of = AnnotationTemplate(Callable, [[input_annotation], str])

endofunctor_from = AnnotationTemplate(Callable, [[input_annotation], Self])

reformer_of = AnnotationTemplate(Callable, [[input_annotation], input_annotation])

merger_of = AnnotationTemplate(Callable, [[input_annotation, input_annotation], input_annotation])

event_for = AnnotationTemplate(Callable, [[], input_annotation])

factory_for = AnnotationTemplate(Callable, [[...], input_annotation])


handler = handler_of[Any]

checker = checker_of[Any]

decorator = reformer_of[Callable]

event = event_for[Any]