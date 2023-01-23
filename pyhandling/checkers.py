from abc import ABC, abstractmethod
from functools import partial
from typing import Self, Any, Iterable, Optional, Callable, Sized

from pyannotating import many_or_one

from pyhandling.annotations import checker


class IChecker(ABC):
    """
    Interface for the validating entity.

    Can be used | and & for grouping with another checker.
    """

    @abstractmethod
    def __or__(self, other: checker) -> Self:
        pass

    @abstractmethod
    def __and__(self, other: checker) -> Self:
        pass

    @abstractmethod
    def __call__(self, resource: Any) -> bool:
        pass


class CheckerKeeper:
    """
    Mixin class for conveniently getting checkers from an input collection and
    unlimited input arguments.
    """

    def __init__(self, checker_resource: many_or_one[checker], *checkers: checker):
        self.checkers = (
            tuple(checker_resource)
            if isinstance(checker_resource, Iterable)
            else (checker_resource, )
        ) + checkers


class UnionChecker(CheckerKeeper, IChecker):
    """
    Checker class delegating check responsibilities to other checkers.

    Specifies the consistency strictness of checkers by the is_strict attribute.

    Throws an error if there are no checkers.
    """

    def __init__(
        self,
        checker_resource: many_or_one[checker],
        *checkers: checker,
        is_strict: bool = False
    ):
        super().__init__(checker_resource, *checkers)
        self.is_strict = is_strict

    @property
    def checkers(self) -> tuple[checker]:
        return self._checkers

    @checkers.setter
    def checkers(self, checkers: Iterable[checker]) -> None:
        self._checkers = tuple(checkers)

        if len(self._checkers) == 0:
            raise AttributeError("UnionChecker.checkers must contain at least one checker")

    def __repr__(self) -> str:
        return "{class_name}[{checker_part}]".format(
            class_name=self.__class__.__name__,
            checker_part=(' & ' if self.is_strict else ' | ').join(
                map(str, self.checkers)
            )
        )

    def __call__(self, resource: Any) -> bool:
        return (all if self.is_strict else any)(
            checker(resource) for checker in self.checkers
        )

    def __or__(self, other: checker) -> Self:
        return self.create_merged_checker_by(self, other, is_strict=False)

    def __ror__(self, other: checker) -> Self:
        return self.create_merged_checker_by(other, self, is_strict=False)

    def __and__(self, other: checker) -> Self:
        return self.create_merged_checker_by(self, other, is_strict=True)

    def __rand__(self, other: checker) -> Self:
        return self.create_merged_checker_by(other, self, is_strict=True)

    @classmethod
    def create_merged_checker_by(
        cls, 
        first_checker: checker, 
        second_checker: checker, 
        *args, 
        is_strict: Optional[bool] = None, 
        **kwargs
    ) -> Self:
        """Method for creating a checker by merging with another."""

        if (
            isinstance(first_checker, UnionChecker)
            and isinstance(second_checker, UnionChecker)
            and first_checker.is_strict is second_checker.is_strict
            and (is_strict is None or is_strict is first_checker.is_strict)
        ):
            first_checkers = cls.__get_checkers_from(first_checker)
            second_checkers = cls.__get_checkers_from(second_checker)

            if is_strict is None:
                is_strict = first_checker.is_strict
        else:
            first_checkers, second_checkers = (first_checker, ), (second_checker, )

        return cls(
            *first_checkers,
            *second_checkers,
            *args,
            **({'is_strict': is_strict} if is_strict is not None else dict()),
            **kwargs 
        )

    @staticmethod
    def __get_checkers_from(checker: checker) -> Iterable[checker]:
        return (
            checker.checkers
            if isinstance(checker, UnionChecker)
            else (checker, )
        )


class CheckerUnionDelegatorMixin:
    """
    Mixin class to implement | and &.

    Creates new grouping checkers when grouped with another checker by delegating
    creation to the appropriate _non_strict_union_checker_factory and
    _strict_union_checker_factory factories.

    Uses UnionChecker by default.
    """

    _non_strict_union_checker_factory: Callable[[Iterable[checker]], IChecker] = UnionChecker
    _strict_union_checker_factory: Callable[[Iterable[checker]], IChecker] = partial(
        UnionChecker,
        is_strict=True
    )

    def __or__(self, other: checker) -> IChecker:
        return self._non_strict_union_checker_factory((self, other))

    def __ror__(self, other: checker) -> Self:
        return self._non_strict_union_checker_factory((other, self))

    def __and__(self, other: checker) -> IChecker:
        return self._strict_union_checker_factory((self, other))

    def __rand__(self, other: checker) -> Self:
        return self._strict_union_checker_factory((other, self))


class Negationer(CheckerUnionDelegatorMixin, IChecker):
    """Proxy checker class to emulate the \"not\" operator."""

    def __init__(self, checker: checker):
        self.checker = checker

    def __repr__(self) -> str:
        return f"<not {self.checker}>"

    def __call__(self, resource: Any) -> bool:
        return not self.checker(resource)


class TypeChecker(CheckerUnionDelegatorMixin, IChecker):
    """
    Class that implements checking whether an object conforms to certain types

    Has the is_correctness_under_supertype flag attribute that specifies whether
    the object type should match the all support types.
    """

    def __init__(
        self,
        correct_type_resource: many_or_one[type],
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

    def __call__(self, resource: Any) -> bool:
        return (
            len(self.correct_types) > 0
            and (all if self.is_correctness_under_supertype else any)(
                isinstance(resource, correct_type)
                for correct_type in self.correct_types
            )
        )


class LengthChecker(CheckerUnionDelegatorMixin, IChecker):
    """
    Checker class for the presence of the length of the collection in a certain
    interval.

    Specifies a length range from an input length or sets of lengths from which
    the length range of minimum and maximum values will be made.

    Optionally includes the end value of the length in the length range by the
    value of the is_end_inclusive attribute.
    """

    def __init__(self, required_length: many_or_one[int], *, is_end_inclusive: bool = True):
        self._required_length = tuple(
            (min(required_length), max(required_length))
            if isinstance(required_length, Iterable)
            else (0, required_length)
        )
        self._is_end_inclusive = is_end_inclusive
        self._update_required_length_range()

    @property
    def required_length(self) -> tuple[int]:
        return self._required_length

    @required_length.setter
    def required_length(self, required_length: Iterable[int]) -> None:
        self._required_length = tuple(required_length)
        self._update_required_length_range()

    @property
    def is_end_inclusive(self) -> bool:
        return self._is_end_inclusive

    @is_end_inclusive.setter
    def is_end_inclusive(self, is_end_inclusive: bool) -> None:
        self._is_end_inclusive = is_end_inclusive
        self._update_required_length_range()

    @property
    def required_length_range(self) -> range:
        return self._required_length_range

    def __repr__(self) -> str:
        return "{class_name}({length_part})".format(
            class_name=self.__class__.__name__,
            length_part="{min_length_part}{max_length}".format(
                min_length_part=(
                    f"{self.required_length_range.start}, "
                    if self.required_length_range.start > 0
                    else str()
                ),
                max_length=self.required_length_range.stop - 1
            )
        )

    def __call__(self, collection: Sized) -> bool:
        return len(collection) in self.required_length_range

    def _update_required_length_range(self) -> None:
        self._required_length_range = range(
            self.required_length[0],
            self.required_length[1] + (1 if self.is_end_inclusive else 0)
        )