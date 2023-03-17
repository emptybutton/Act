from functools import reduce
from itertools import chain
from typing import Callable, Any, Iterable, Type
from unittest import TestCase

from pyannotating import many_or_one

from pyhandling.tools import ArgumentPack


__all__ = ("calling_test_of", "calling_test_from")


def _calling_test_method_for(
    action: Callable, 
    expected_result: Any,
    arguments_of_calls: many_or_one[ArgumentPack] = ArgumentPack()
) -> Callable[[TestCase], None]:
    """Function to create a `TestCase` method to test an input action calling."""

    if not isinstance(arguments_of_calls, Iterable):
        arguments_of_calls = (arguments_of_calls, )

    def testing_method(test_case: TestCase, action=action, arguments=arguments_of_calls, expected_result=expected_result) -> None:
        result = reduce(lambda action, pack: pack.call(action), chain([action], arguments))
        test_case.assertEqual(result, expected_result)

    return testing_method


def calling_test_from(*cases: tuple[Callable, Any, many_or_one[ArgumentPack]]) -> Type[TestCase]:
    """
    Function to create a `TestCase` type with generated methods that test
    calling specific actions.

    When passing multiple argument packs, unpacks each subsequent pack into the
    expected callable result of calling the previous argument pack.
    """

    generated_test_case_type = type(
        f"TestCalling",
        (TestCase, ),
        {
            f"test_action_that_{case_index}": _calling_test_method_for(*case)
            for case_index, case in enumerate(cases)
        }
        | {
            "__doc__": (
                """
                `TestCase` class generated from
                `pyhandling.testing.calling_test_from` for some actions
                """
            )
        }
    )

    return generated_test_case_type


def calling_test_of(
    action: Callable, 
    expected_result: Any,
    arguments_of_calls: many_or_one[ArgumentPack] = ArgumentPack()
) -> Type[TestCase]:
    """
    Function generating `TestCase` type like
    `pyhandling.testing.calling_test_from` but with one generated method.
    """

    return calling_test_from((action, expected_result, arguments_of_calls))