from typing import Callable, Any, Self, TypeVar, TypeVarTuple

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation


dirty = FormalAnnotation(
    """
    Formal annotation to indicate the dirtyness of a function or any other
    callable object.
    """
)

not_required = FormalAnnotation(
    """Formal annotation to indicate an optional parameter in a function."""
)


handler_of = AnnotationTemplate(Callable, [[input_annotation], Any])

checker_of = AnnotationTemplate(Callable, [[input_annotation], bool])

formatter_of = AnnotationTemplate(Callable, [[input_annotation], str])

reformer_of = AnnotationTemplate(Callable, [[input_annotation], input_annotation])

merger_of = AnnotationTemplate(Callable, [[input_annotation, input_annotation], input_annotation])

event_for = AnnotationTemplate(Callable, [[], input_annotation])

factory_for = AnnotationTemplate(Callable, [[...], input_annotation])


handler = handler_of[Any]

checker = checker_of[Any]

decorator = reformer_of[Callable]

event = event_for[Any]

binder = Callable[[Callable, ...], Callable]


FuncT = TypeVar("FuncT", bound=Callable)

ArgumentsT = TypeVarTuple("ArgumentsT")

ResultT = TypeVar("ResultT")

