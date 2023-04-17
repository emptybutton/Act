from types import UnionType
from typing import Callable, Any, TypeAlias, TypeVar, ParamSpec, Iterable, Self, Iterator, Tuple, _CallableGenericAlias, _CallableType, _UnionGenericAlias

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation, Special

from pyhandling.scoping import value_of


__all__ = (
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
    "FirstT",
    "SecondT",
    "ThirdT",
    "FourthT",
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
    "PointT",
    "AtomT",
    "AtomizableT",
    "CallableFormalAnnotation",
    "notes_of",
    "dirty",
    "pure",
    "action_of",
)


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

FirstT = TypeVar("FirstT")

SecondT = TypeVar("SecondT")

ThirdT = TypeVar("ThirdT")

FourthT = TypeVar("FourthT")

ResultT = TypeVar("ResultT")

PositiveConditionResultT = TypeVar("PositiveConditionResultT")

NegativeConditionResultT = TypeVar("NegativeConditionResultT")

ErrorHandlingResultT = TypeVar("ErrorHandlingResultT")

ErrorT = TypeVar("ErrorT", bound=Exception)

TypeT = TypeVar("TypeT", bound=type)

ContextT = TypeVar("ContextT")

KeyT = TypeVar('KeyT')

MappedT = TypeVar("MappedT")

FlagT = TypeVar("FlagT", bound='Flag')

PointT = TypeVar("PointT")

AtomT = TypeVar("AtomT")
AtomizableT = TypeVar("AtomT", bound="Atomizable")


class CallableFormalAnnotation(FormalAnnotation):
    def __call__(self, value: ValueT) -> ValueT:
        notes = (*notes_of(value), self)

        try:
            value.__notes__ = notes
        except AttributeError:
            ...

        return value


def notes_of(value: Any) -> Tuple:
    return tuple(value.__notes__) if hasattr(value, "__notes__") else tuple()


dirty = CallableFormalAnnotation(
    """
    Formal annotation to indicate that an action interacts with any state or
    indicate value output from such action.
    """
)

pure = CallableFormalAnnotation(
    """
    Formal annotation to indicate that an action always returns the same
    result with the same arguments and does not interact with any state or
    indicate value output from such action.
    """
)


class _CallableConstructor:
    def __getitem__(self, annotations: Special[Iterable]) -> _CallableGenericAlias | _CallableType:
        if not isinstance(annotations, _AnnotationsT):
            annotations = (annotations, )

        annotations = tuple(
            self[annotation] if isinstance(annotation, _AnnotationsT) else annotation
            for annotation in annotations
        )

        return self._annotation_from(annotations)

    def _annotation_from(self, annotations: Tuple) -> _CallableGenericAlias | _CallableType:
        if len(annotations) == 0:
            return Callable
        elif len(annotations) == 1:
            return Callable[[annotations[0]], Any]
        elif len(annotations) == 2:
            return Callable[[annotations[0]], annotations[1]]
        else:
            return Callable[
                [annotations[0]],
                self._annotation_from(annotations[1:]),
            ]


action_of = _CallableConstructor()


_AnnotationsT: TypeAlias = list | tuple