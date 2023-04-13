from functools import partial
from typing import Callable, Any

from pyhandling.arguments import ArgumentPack
from pyhandling.synonyms import *
from pyhandling.testing import calling_test_case_of
from tests.mocks import CustomContext

from pytest import mark, raises


test_returned = calling_test_case_of((lambda: returned(None), None))


test_raise_ = calling_test_case_of((
    lambda: with_context_manager_by(lambda error: raises(type(error)), raise_)(Exception()),
    None,
))


test_assert_ = calling_test_case_of(
    (lambda: assert_(16), None),
    (
        lambda: with_context_manager_by(lambda _: raises(AssertionError), assert_)(None),
        None,
    ),
)


test_collection_of = calling_test_case_of(
    (lambda: collection_of(1, 2, 3), (1, 2, 3)),
    (lambda: collection_of(), tuple()),
)


test_with_unpacking = calling_test_case_of((
    lambda: with_unpacking(lambda a, b, c: (c, b, a))([1, 2, 3]),
    (3, 2, 1),
))


test_with_keyword_unpacking = calling_test_case_of((
    lambda: with_keyword_unpacking(lambda a, b, c: (c, b, a))(dict(a=1, b=2, c=3)),
    (3, 2, 1),
))


test_to_context_manager = calling_test_case_of(
    (lambda: to_context_manager(lambda _: _)(CustomContext(None)), None),
    (lambda: to_context_manager(lambda n: n + 6)(CustomContext(10)), 16),
)