from typing import Callable, Any, TypeAlias, TypeVar, ParamSpec

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation


__all__ = (
    "dirty",
    "handler_of",
    "checker_of",
    "formatter_of",
    "transformer_to",
    "reformer_of",
    "merger_of",
    "event_for",
    "action_for",
    "one_value_action",
    "checker",
    "decorator",
    "event",
    "ActionT",
    "P",
    "ValueT",
    "ObjectT",
    "ResultT",
    "KeyT",
    "ErrorT",
    "TypeT",
    "ContextT",
    "PositiveConditionResultT",
    "NegativeConditionResultT",
    "ErrorHandlingResultT",
    "MappedT",
    "FlagT",
    "AtomT",
)


dirty = FormalAnnotation(
    """
    Formal annotation to indicate the dirtyness of a function or any other
    callable object.
    """
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


one_value_action = reformer_of[Any]

checker = checker_of[Any]

decorator = reformer_of[Callable]

event = event_for[Any]


ActionT = TypeVar("ActionT", bound=Callable)

P = ParamSpec('P')

ValueT = TypeVar("ValueT")

ObjectT = TypeVar("ObjectT")

ResultT = TypeVar("ResultT")

PositiveConditionResultT = TypeVar("PositiveConditionResultT")

NegativeConditionResultT = TypeVar("NegativeConditionResultT")

ErrorHandlingResultT = TypeVar("ErrorHandlingResultT")

ErrorT = TypeVar("ErrorT", bound=Exception)

TypeT = TypeVar("TypeT", bound=type)

ContextT = TypeVar("ContextT")

KeyT = TypeVar('KeyT')

MappedT = TypeVar("MappedT")

FlagT = TypeVar("FlagT", bound='Flag')FlagT = TypeVar("FlagT", bound='Flag')
