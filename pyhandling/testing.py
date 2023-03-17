from functools import reduce
from itertools import chain
from typing import Callable, Any, Iterable, Type

from pyannotating import many_or_one

from pyhandling.tools import ArgumentPack


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
