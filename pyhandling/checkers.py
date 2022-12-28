from abc import ABC, abstractmethod

from typing import NewType, Callable, Self, Iterable


Checker = NewType('Checker', Callable[[any], bool])


class IChecker(ABC):
    """
    Interface for the validating entity.

    Can be used | and & for grouping with another checker.
    """

    @abstractmethod
    def __or__(self, other: Checker) -> Self:
        pass

    @abstractmethod
    def __and__(self, other: Checker) -> Self:
        pass

    @abstractmethod
    def __call__(self, resource: any) -> bool:
        pass


class CheckerKeeper:
    """
    Mixin class for conveniently getting checkers from an input collection and
    unlimited input arguments.
    """

    def __init__(self, checker_resource: Checker | Iterable[Checker], *checkers: Checker):
        self.checkers = (
            tuple(checker_resource)
            if isinstance(checker_resource, Iterable)
            else (checker_resource, )
        ) + checkers


class Anyer(CheckerKeeper, IChecker):
    """
    Checker class not strictly delegating check responsibilities to other checkers.

    It is an adapter for \"any\" function.

    Strictly related to Aller as it uses it as a factory for & result.
    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{' | '.join(map(str, self.checkers))}]"

    def __call__(self, resource: any) -> bool:
        return any(checker(resource) for checker in self.checkers)

    def __or__(self, other: Checker) -> Self:
        return self.__class__(
            *self.checkers,
            *(
                other.checkers
                if isinstance(other, Anyer)
                else (other, )
            )
        )

    def __and__(self, other: Checker) -> IChecker:
        return Aller(self, other)


class Aller(CheckerKeeper, IChecker):
    """
    Checker class strictly delegating check responsibilities to other checkers.

    It is an adapter for \"all\" function.

    Strictly related to Anyer as it uses it as a factory for | result.
    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{' & '.join(map(str, self.checkers))}]"

    def __call__(self, resource: any) -> bool:
        return all(checker(resource) for checker in self.checkers)

    def __or__(self, other: Checker) -> IChecker:
        return Anyer(self, other)

    def __and__(self, other: Checker) -> Self:
        return self.__class__(
            *self.checkers,
            *(
                other.checkers
                if isinstance(other, Aller)
                else (other, )
            )
        )


class CheckerUnionDelegatorMixin:
    """
    Mixin class to implement | and &.

    Creates new grouping checkers when grouped with another checker by delegating
    creation to the appropriate _non_strict_union_checker_factory and
    _strict_union_checker_factory factories.

    By default associated with Anyer and Aller.
    """

    _non_strict_union_checker_factory: Callable[[Iterable[Checker]], IChecker] = Anyer
    _strict_union_checker_factory: Callable[[Iterable[Checker]], IChecker] = Aller

    def __or__(self, other: Checker) -> IChecker:
        return self._non_strict_union_checker_factory((self, other))

    def __and__(self, other: Checker) -> IChecker:
        return self._strict_union_checker_factory((self, other))


class Negationer(CheckerUnionDelegatorMixin, IChecker):
    """Proxy checker class to emulate the \"not\" operator."""

    def __init__(self, checker: Checker):
        self.checker = checker

    def __repr__(self) -> str:
        return f"<not {self.checker}>"

    def __call__(self, resource: any) -> bool:
        return not self.checker(resource)


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