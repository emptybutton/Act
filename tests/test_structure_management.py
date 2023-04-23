from typing import Iterable, Any

from pytest import mark

from pyhandling.testing import calling_test_case_of
from pyhandling.structure_management import *


@mark.parametrize(
    'input_collection, result_collection',
    [
        ([1, 2, 3], (1, 2, 3)),
        ([1, 2, (3, 4)], (1, 2, 3, 4)),
        ([1, 2, (3, (4, 5))], (1, 2, 3, (4, 5))),
        (tuple(), tuple()),
        (str(), tuple()),
    ]
)
def test_with_opened_items(input_collection: Iterable, result_collection: tuple):
    assert with_opened_items(input_collection) == result_collection


@mark.parametrize(
    'resource, result_collection',
    [
        (42, (42, )),
        (str(), (str(), )),
        (tuple(), (tuple(), )),
        ((1, 2, 3), ((1, 2, 3), ))
    ]
)
def test_in_collection(resource: Any, result_collection: tuple):
    assert in_collection(resource) == result_collection


@mark.parametrize(
    "input_value, result",
    [
        (42, (42, )),
        (None, (None, )),
        ([1, 2, 3], (1, 2, 3)),
        (map(lambda x: x ** 2, [4, 8, 16]), (16, 64, 256)),
        ((3, 9, 12), (3, 9, 12)),
        (tuple(), tuple()),
        (list(), tuple()),
        ('Hello', ('H', 'e', 'l', 'l', 'o'))
    ]
)
def test_as_collection(input_value: Any, result: tuple):
    assert as_collection(input_value) == result


test_tmap = calling_test_case_of((
    lambda: tmap(lambda i: i + 1, range(9)), tuple(range(1, 10))
))


test_tfilter = calling_test_case_of((
    lambda: tfilter(lambda i: i % 2 == 0, range(11)), tuple(range(0, 11, 2))
))

test_tzip = calling_test_case_of((
    lambda: tzip(['a', 'b'], range(10)), (('a', 0), ('b', 1))
))
