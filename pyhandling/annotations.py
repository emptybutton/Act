from typing import Callable, Any, TypeAlias, TypeVar, TypeVarTuple

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation


__all__ = (
    "dirty", "not_required", "handler_of", "checker_of", "formatter_of",
    "transformer_to", "reformer_of", "merger_of", "event_for", "action_for",
    "atomic_action","checker", "decorator", "event", "binder", "ActionT",
    "ArgumentsT", "ValueT", "ObjectT", "ResultT", "KeyT", "ErrorT", "ContextT",
    "PositiveConditionResultT", "NegativeConditionResultT", "ErrorHandlingResultT"
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

transformer_to = AnnotationTemplate(Callable, [[Any], input_annotation])

reformer_of = AnnotationTemplate(Callable, [[input_annotation], input_annotation])

merger_of = AnnotationTemplate(Callable, [
    [input_annotation, input_annotation], input_annotation
])

event_for = AnnotationTemplate(Callable, [[], input_annotation])

action_for = AnnotationTemplate(Callable, [[...], input_annotation])


atomic_action: TypeAlias = reformer_of[Any]

checker: TypeAlias = checker_of[Any]

decorator: TypeAlias = reformer_of[Callable]

event: TypeAlias = event_for[Any]

binder: TypeAlias = Callable[[Callable, ...], Callable]


ActionT = TypeVar("ActionT", bound=Callable)

ArgumentsT = TypeVarTuple("ArgumentsT")

ValueT = TypeVar("ValueT")

ObjectT = TypeVar("ObjectT")

ResultT = TypeVar("ResultT")

KeyT = TypeVar("KeyT")

ErrorT = TypeVar("ErrorT", bound=Exception)

ContextT = TypeVar("ContextT")

PositiveConditionResultT = TypeVar("PositiveConditionResultT")

NegativeConditionResultT = TypeVar("NegativeConditionResultT")

ErrorHandlingResultT = TypeVar("ErrorHandlingResultT")