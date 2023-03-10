from typing import Callable, Any, TypeVar, TypeVarTuple

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation


__all__ = (
    "dirty", "not_required", "handler_of", "checker_of", "formatter_of",
    "reformer_of", "merger_of", "event_for", "factory_for", "handler", "checker",
    "decorator", "event", "binder", "ActionT", "ArgumentsT", "ResourceT",
    "ObjectT", "ResultT", "KeyT", "ErrorT", "PositiveResultT",
    "NegativeConditionResultT", "ErrorHandlingResultT"
)


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


ActionT = TypeVar("ActionT", bound=Callable)

ArgumentsT = TypeVarTuple("ArgumentsT")

ResourceT = TypeVar("ResourceT")

ObjectT = TypeVar("ObjectT")

ResultT = TypeVar("ResultT")

KeyT = TypeVar("KeyT")

ErrorT = TypeVar("ErrorT", bound=Exception)

PositiveConditionResultT = TypeVar("PositiveResultT")

NegativeConditionResultT = TypeVar("NegativeConditionResultT")

ErrorHandlingResultT = TypeVar("ErrorHandlingResultT")