from typing import Iterable, Any

from pytest import mark

from pyhandling.testing import case_of
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
def test_flat(input_collection: Iterable, result_collection: tuple):
    assert flat(input_collection) == result_collection


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


test_tmap = case_of((
    lambda: tmap(lambda i: i + 1, range(9)), tuple(range(1, 10))
))


test_tfilter = case_of((
    lambda: tfilter(lambda i: i % 2 == 0, range(11)), tuple(range(0, 11, 2))
))

test_tzip = case_of((
    lambda: tzip(['a', 'b'], range(10)), (('a', 0), ('b', 1))
))
