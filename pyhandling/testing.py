from typing import TypeAlias, Any, Callable, Type
from unittest import TestCase

from pyhandling.annotations import event


__all__ = ("calling_test_case_of", )


test_case_pack: TypeAlias = tuple[event, Any]


def _calling_test_method_of(test_pack: test_case_pack) -> Callable[[TestCase], None]:
    def testing_method(test_case: TestCase) -> None:
        test_case.assertEqual(test_pack[0](), test_pack[1])

    return testing_method



def calling_test_case_of(*test_packs: test_case_pack) -> Type[TestCase]:
    return type(
        f"TestByCalling",
        (TestCase, ),
        {
            f"test_action_that_{test_pack_index}": _calling_test_method_of(test_pack)
            for test_pack_index, test_pack in enumerate(test_packs)
        }
        | {
            "__doc__": (
                """
                `TestCase` class generated from
                `pyhandling.testing.calling_test_case_of` for some actions
                """
            )
        }
    )