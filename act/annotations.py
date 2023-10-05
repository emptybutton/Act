from functools import reduce
from operator import attrgetter
from types import UnionType
from typing import (
    Callable, Any, TypeAlias, TypeVar, ParamSpec, TypeVarTuple, Iterable, Tuple,
    Self, Concatenate, _CallableGenericAlias, _CallableType, _UnionGenericAlias
)

from pyannotating import (
    FormalAnnotation, AnnotationTemplate, input_annotation, Special
)

from act.errors import UnionError
from act.representations import code_like_repr_of


__all__ = (
    "Annotation",
    "Cn",
    "Special",
    "reformer_of",
    "merger_of",
    "ArgumentsT",
    "ActionT",
    "ErrorT",
    "TypeT",
    "FlagT",
    "AtomizableT",
    "ContextualT",
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
    "Pm",
    "PmA",
    "PmB",
    "PmC",
    "PmD",
    "PmE",
    "PmF",
    "PmG",
    "PmH",
    "PmI",
    "PmJ",
    "PmK",
    "PmL",
    "PmM",
    "PmN",
    "PmO",
    "PmP",
    "PmQ",
    "PmR",
    "PmS",
    "PmT",
    "PmU",
    "PmV",
    "PmW",
    "PmX",
    "PmY",
    "PmZ",
    "CommentAnnotation",
    "CallableFormalAnnotation",
    "notes_of",
    "dirty",
    "pure",
    "action_of",
    "Union",
    "Unia",
)


Annotation: TypeAlias = Any

Cn = Concatenate

reformer_of = AnnotationTemplate(
    Callable, [[input_annotation], input_annotation]
)

merger_of = AnnotationTemplate(Callable, [
    [input_annotation, input_annotation], input_annotation
])


ArgumentsT = TypeVarTuple("ArgumentsT")

ActionT = TypeVar("ActionT", bound=Callable)

ErrorT = TypeVar("ErrorT", bound=Exception)

TypeT = TypeVar("TypeT", bound=type)

FlagT = TypeVar("FlagT", bound='Flag')

AtomizableT = TypeVar("AtomT", bound="Atomizable")

ContextualT = TypeVar("ContextualT", bound="ContextualForm")


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

Pm = ParamSpec('Pm')
PmA = ParamSpec('PmA')
PmB = ParamSpec('PmB')
PmC = ParamSpec('PmC')
PmD = ParamSpec('PmD')
PmE = ParamSpec('PmE')
PmF = ParamSpec('PmF')
PmG = ParamSpec('PmG')
PmH = ParamSpec('PmH')
PmI = ParamSpec('PmI')
PmJ = ParamSpec('PmJ')
PmK = ParamSpec('PmK')
PmL = ParamSpec('PmL')
PmM = ParamSpec('PmM')
PmN = ParamSpec('PmN')
PmO = ParamSpec('PmO')
PmP = ParamSpec('PmP')
PmQ = ParamSpec('PmQ')
PmR = ParamSpec('PmR')
PmS = ParamSpec('PmS')
PmT = ParamSpec('PmT')
PmU = ParamSpec('PmU')
PmV = ParamSpec('PmV')
PmW = ParamSpec('PmW')
PmX = ParamSpec('PmX')
PmY = ParamSpec('PmY')
PmZ = ParamSpec('PmZ')


class CommentAnnotation:
    """Class for annotation as comments."""

    def __init__(self, name: str, *, args: Iterable = tuple()):
        self._name = name
        self._args = tuple(args)

    def __repr__(self) -> str:
        return f"~{self._name}{{}}".format(
            "[{}]".format(', '.join(map(code_like_repr_of, self._args)))
            if len(self._args) > 0
            else str()
        )

    def __hash__(self) -> int:
        return hash(type(self)) + hash(self._name) + hash(self._args)

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

    def __and__(self, other: Any):
        return Unia[self, other]

    def __rand__(self, other: Any):
        return Unia[other, self]


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


_AnnotationsT: TypeAlias = list | tuple


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


class Union:
    __args__ = property(attrgetter("_annotations"))

    def __new__(cls, *annotations: Special[Self], **kwargs) -> Self:
        if len(annotations) == 1:
            return annotations[0]
        elif len(annotations) == 0:
            raise UnionError("ValueUnion without annotations")
        else:
            return super().__new__(cls)

    def __init__(self, *annotations):
        self._annotations = sum(
            tuple(map(self._annotation_of, annotations)), tuple()
        )

    def __repr__(self) -> str:
        return ' | '.join(map(code_like_repr_of, self._annotations))

    def __class_getitem__(cls, annotations: Special[tuple]) -> Self:
        return cls(*(
            annotations
            if isinstance(annotations, tuple)
            else (annotations, )
        ))

    def __instancecheck__(self, instance) -> bool:
        return self._annotations and any(
            isinstance(instance, annotation)
            for annotation in self._annotations
        )

    def __or__(self, other: Any) -> Self:
        return type(self)(self, other)

    def __ror__(self, other: Any) -> Self:
        return type(self)(other, self)

    @staticmethod
    def _annotation_of(annotation: Any) -> tuple:
        return (
            annotation.__args__
            if isinstance(annotation, Union | UnionType | _UnionGenericAlias)
            else (annotation, )
        )


class Unia:
    """
    Union type with `and` nature i.e a value being checked must be a descendant
    of all types passed to an Unia.

    To create using indexer (`[]`).
    """

    annotations = property(attrgetter("_annotations"))

    def __new__(cls, *annotations: Special[Self], **kwargs) -> Self:
        if len(annotations) == 1:
            return annotations[0]
        elif len(annotations) == 0:
            raise UnionError("Unia without annotations")
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

    def __hash__(self) -> int:
        return reduce(
            lambda sum_, a: sum_ + (hash(a) if hasattr(a, "__hash__") else id(a)),
            [hash(type(self)), *self._annotations],
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

    def __subclasscheck__(self, type_: type) -> bool:
        return all(
            issubclass(type_, annotation) for annotation in self._annotations
        )

    def __or__(self, other: Any) -> Union:
        return Union[self, other]

    def __ror__(self, other: Any) -> Union:
        return Union[other, self]

    @staticmethod
    def _annotations_from(annotations: Tuple[Special[Self]]) -> tuple:
        result_annotations = list()

        for annotation in annotations:
            if isinstance(annotation, Unia):
                result_annotations.extend(annotation.annotations)
            else:
                result_annotations.append(annotation)

        return tuple(result_annotations)
