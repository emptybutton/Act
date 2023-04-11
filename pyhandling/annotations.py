from types import UnionType
from typing import Callable, Any, TypeAlias, TypeVar, ParamSpec, Iterable, Self, Iterator, Tuple, _CallableGenericAlias, _CallableType, _UnionGenericAlias

from pyannotating import FormalAnnotation, AnnotationTemplate, input_annotation, Special

from pyhandling.scoping import value_of


__all__ = (
    "dirty",
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
    "t",
    "action_of",
)


dirty = FormalAnnotation(
    """Formal annotation to indicate the dirtyness of an action."""
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


class _AnnotationSequence:
    def __init__(self, annotations: Iterable = tuple()):
        self._annotations = tuple(annotations)

    def __repr__(self) -> str:
        return f"Callable{self._internal_repr()}"

    def __iter__(self) -> Iterator:
        return iter(self._annotations)

    def __getitem__(self, annotation: Any) -> Self:
        return type(self)([*self._annotations, annotation])

    def __rshift__(self, other: Self) -> Self:
        return type(self)((*self._annotations, *other._annotations))

    def _internal_repr(self) -> str:
        return f"[{' -> '.join(map(self.__fromatted, self._annotations))}]"

    @staticmethod
    def __fromatted(annotation: Any) -> str:
        if isinstance(annotation, UnionType | _UnionGenericAlias):
            return ' | '.join(map(str, annotation.__args__))

        elif isinstance(annotation, type):
            return annotation.__name__

        elif isinstance(annotation, _AnnotationSequence):
            return annotation._internal_repr()

        else:
            return str(annotation)


t = _AnnotationSequence()


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


_AnnotationsT: TypeAlias = list | tuple | _AnnotationSequence