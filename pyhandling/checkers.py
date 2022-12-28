
from typing import NewType, Callable, Self, Iterable


Checker = NewType('Checker', Callable[[any], bool])
class TypeChecker(CheckerUnionDelegatorMixin, IChecker):
    """
    Class that implements checking whether an object conforms to certain types

    Has the is_correctness_under_supertype flag attribute that specifies whether
    the object type should match the all support types.
    """

    def __init__(
        self,
        correct_type_resource: Iterable[type] | type,
        *,
        is_correctness_under_supertype: bool = False
    ):
        self.is_correctness_under_supertype = is_correctness_under_supertype
        self.correct_types = (
            correct_type_resource
            if isinstance(correct_type_resource, Iterable)
            else (correct_type_resource, )
        )

    def __repr__(self) -> str:
        return "{class_name}({formatted_types})".format(
            class_name=self.__class__.__name__,
            formatted_types=(' | ' if not self.is_correctness_under_supertype else ' & ').join(
                map(
                    lambda type_: (type_.__name__ if hasattr(type_, '__name__') else str(type_)),
                    self.correct_types
                )
            )
        )

    def __call__(self, resource: any) -> bool:
        return (
            len(self.correct_types) > 0
            and (all if self.is_correctness_under_supertype else any)(
                isinstance(resource, correct_type)
                for correct_type in self.correct_types
            )
        )