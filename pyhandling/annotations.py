from operator import attrgetter
from typing import (
    Callable, Any, TypeAlias, TypeVar, ParamSpec, TypeVarTuple, Iterable,
    Tuple, Self, Union, _CallableGenericAlias, _CallableType
)

from pyannotating import (
    FormalAnnotation, AnnotationTemplate, input_annotation, Special
)

from pyhandling.errors import UniaError
from pyhandling.representations import action_repr_of


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
    "Pm",
    "ArgumentsT",
    "ActionT",
    "ErrorT",
    "TypeT",
    "FlagT",
    "AtomizableT",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
    "CommentAnnotation",
    "CallableFormalAnnotation",
    "notes_of",
    "dirty",
    "pure",
    "action_of",
    "Unia",
)


checker_of = AnnotationTemplate(Callable, [[input_annotation], bool])

formatter_of = AnnotationTemplate(Callable, [[input_annotation], str])

transformer_to = AnnotationTemplate(Callable, [[Any], input_annotation])

reformer_of = AnnotationTemplate(
    Callable, [[input_annotation], input_annotation]
)

merger_of = AnnotationTemplate(Callable, [
    [input_annotation, input_annotation], input_annotation
])

event_for = AnnotationTemplate(Callable, [[], input_annotation])

action_for = AnnotationTemplate(Callable, [[...], input_annotation])


one_value_action = reformer_of[Any]

checker = checker_of[Any]

decorator = reformer_of[Callable]

event = event_for[Any]


Pm = ParamSpec('Pm')

ArgumentsT = TypeVarTuple("ArgumentsT")

ActionT = TypeVar("ActionT", bound=Callable)

ErrorT = TypeVar("ErrorT", bound=Exception)

TypeT = TypeVar("TypeT", bound=type)

FlagT = TypeVar("FlagT", bound='Flag')

AtomizableT = TypeVar("AtomT", bound="Atomizable")


A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')
E = TypeVar('E')
F = TypeVar('F')
G = TypeVar('G')
H = TypeVar('H')
I = TypeVar('I')
J = TypeVar('J')
K = TypeVar('K')
L = TypeVar('L')
M = TypeVar('M')
N = TypeVar('N')
O = TypeVar('O')
P = TypeVar('P')
Q = TypeVar('Q')
R = TypeVar('R')
S = TypeVar('S')
T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')
W = TypeVar('W')
X = TypeVar('X')
Y = TypeVar('Y')
Z = TypeVar('Z')


class CommentAnnotation:
    """Class for annotation as comments."""

    def __init__(self, name: str, *, args: Iterable = tuple()):
        self._name = name
        self._args = tuple(args)

    def __repr__(self) -> str:
        return f"~{self._name}{{}}".format(
            "[{}]".format(', '.join(map(action_repr_of, self._args)))
            if len(self._args) > 0
            else str()
        )

    def __eq__(self, other: Special[Self]) -> bool:
        return (
            isinstance(other, CommentAnnotation)
            and self._name == other._name
            and self._args == other._args
        )

    def __getitem__(self, value_or_values: Special[tuple]) -> Self:
        return type(self)(
            self._name,
            args=(
                *self._args,
                *(
                    value_or_values
                    if isinstance(value_or_values, tuple)
                    else (value_or_values, )
                ),
            ),
        )

    def __or__(self, other: Any):
        return Union[self, other]

    def __ror__(self, other: Any):
        return Union[other, self]


class CallableFormalAnnotation(FormalAnnotation):
    """
    `FormalAnnotation` class for annotation via call.

    Annotating instance is stored in an annotated value as a reference in the
    `__notes__` attribute when called.

    For safe interaction with `__notes__` see `notes_of`.
    """

    def __call__(self, value: V) -> V:
        notes = (*notes_of(value), self)

        try:
            value.__notes__ = notes
        except AttributeError:
            ...

        return value


def notes_of(value: Any) -> Tuple:
    """
    Function to get annotation notes from an input value.

    Returns notes from the `__notes__` attribute, if present.
    """

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
    """
    Class for generating a ceoidal `Callable` annotation from unconstrained
    input annotations.

    "Called" via `[]` call.

    Populates annotations starting from arguments and if there are not enough
    annotations, inserts `Any` i.e.
    ```
    instance[tuple()] == Callable
    instance[int] == Callable[[int], Any]
    instance[int, str] == Callable[[int], str]
    ```

    Restricts one `Callable` annotation to only one argument by chaining
    `Callable` that return other `Callable` i.e.
    ```
    instance[int, str, float] == Callable[[int], Callable[[str], float]]
    instance[int, str, float, set] == (
        Callable[[int], Callable[[str], Callable[[float], set]]]
    )
    ```
    """

    def __getitem__(
        self,
        annotations: Special[Iterable],
    ) -> _CallableGenericAlias | _CallableType:
        if not isinstance(annotations, _AnnotationsT):
            annotations = (annotations, )

        annotations = tuple(
            (
                self[annotation]
                if isinstance(annotation, _AnnotationsT)
                else annotation
            )
            for annotation in annotations
        )

        return self._annotation_from(annotations)

    def _annotation_from(
        self,
        annotations: Tuple,
    ) -> _CallableGenericAlias | _CallableType:
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


class Unia:
    annotations = property(attrgetter("_annotations"))

    def __new__(cls, *annotations: Special[Self], **kwargs) -> Self:
        if len(annotations) == 1:
            return annotations[0]
        elif len(annotations) == 0:
            raise UniaError("Unia without annotations")
        else:
            return super().__new__(cls)

    def __init__(self, *annotations: Special[Self]) -> None:
        self._annotations = self._annotations_from(annotations)

    def __repr__(self) -> str:
        return ' & '.join(
            (
                annotation.__name__
                if isinstance(annotation, type)
                else str(annotation)
            )
            for annotation in self._annotations
        )

    def __class_getitem__(cls, annotation_or_annotations: Special[tuple]) -> Self:
        return cls(*(
            annotation_or_annotations
            if isinstance(annotation_or_annotations, tuple)
            else (annotation_or_annotations, )
        ))

    def __eq__(self, other: Special[Self]) -> bool:
        return isinstance(other, Unia) and other.annotations == self.annotations

    def __instancecheck__(self, instance: Any) -> bool:
        return all(
            isinstance(instance, annotation) for annotation in self._annotations
        )

    @staticmethod
    def _annotations_from(annotations: Tuple[Special[Self]]) -> tuple:
        result_annotations = list()

        for annotation in annotations:
            if isinstance(annotation, Unia):
                result_annotations.extend(annotation.annotations)
            else:
                result_annotations.append(annotation)

        return tuple(result_annotations)


_AnnotationsT: TypeAlias = list | tuple
