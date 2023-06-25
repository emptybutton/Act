from types import MappingProxyType
from typing import TypeAlias, Any, Callable, Type
from unittest import TestCase

from pyannotating import Subgroup

from act.annotations import event
from act.data_flow import anything


__all__ = ("case_of", "test_case_pack")


test_case_pack: TypeAlias = tuple[event, Any]

_character_numbers = Subgroup(int, lambda number: number in range(0, 10))

_endings_by_ordinal_numbers: MappingProxyType[_character_numbers, str]
_endings_by_ordinal_numbers = MappingProxyType({
    0: 'th',
    1: 'st',
    2: 'nd',
    3: 'rd',
    4: 'th',
    5: 'th',
    6: 'oh',
    7: 'th',
    8: 'oh',
    9: 'th',
})


def _ordinal_of(number: int) -> str:
    return f"{number}{_endings_by_ordinal_numbers[int(str(number)[-1:])]}"


def _calling_test_method_of(
    test_pack: test_case_pack,
) -> Callable[[TestCase], None]:
    def testing_method(test_case: TestCase) -> None:
        test_case.assertEqual(test_pack[0](), test_pack[1])

    return testing_method


def case_of(*test_packs: test_case_pack | event) -> Type[TestCase]:
    """Function to create a `TestCase` type with input tests."""

    return type(
        "TestByCalling",
        (TestCase, ),
        {
            f"test_{_ordinal_of(test_pack_index)}_action": _calling_test_method_of(
                test_pack,
            )
            for test_pack_index, test_pack in enumerate(map(
                lambda p: p if isinstance(p, tuple | list) else (p, anything),
                test_packs,
            ))
        }
        | {
            "__doc__": (
                """
                `TestCase` class generated from
                `act.testing.test_case_of` for some actions
                """
            )
        }
    )
