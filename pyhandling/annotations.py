from typing import (
    Callable, Any, TypeAlias, TypeVar, ParamSpec, TypeVarTuple, Iterable,
    Tuple, _CallableGenericAlias, _CallableType,
)

from pyannotating import (
    FormalAnnotation, AnnotationTemplate, input_annotation, Special
)


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
    "Pm",
    "ArgumentsT",
    "ValueT",
    "ObjectT",
    "RightT",
    "LeftT",
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
    "CallableFormalAnnotation",
    "notes_of",
    "dirty",
    "pure",
    "action_of",
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


ActionT = TypeVar("ActionT", bound=Callable)

Pm = ParamSpec('Pm')

ArgumentsT = TypeVarTuple("ArgumentsT")

ValueT = TypeVar("ValueT")

ObjectT = TypeVar("ObjectT")

RightT = TypeVar("RightT")

LeftT = TypeVar("LeftT")

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


_AnnotationsT: TypeAlias = list | tuple
