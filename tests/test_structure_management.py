from pyhandling.testing import case_of
from pyhandling.structure_management import *


test_as_collection = case_of(
    (lambda: as_collection(42), (42, )),
    (lambda: as_collection(None), (None, )),
    (lambda: as_collection([1, 2, 3]), (1, 2, 3)),
    (lambda: as_collection(map(lambda x: x ** 2, [4, 8, 16])), (16, 64, 256)),
    (lambda: as_collection((3, 9, 12)), (3, 9, 12)),
    (lambda: as_collection(tuple()), tuple()),
    (lambda: as_collection('Hello'), ('H', 'e', 'l', 'l', 'o')),
)


test_tmap = case_of((
    lambda: tmap(lambda i: i + 1, range(9)), tuple(range(1, 10))
))


test_tfilter = case_of((
    lambda: tfilter(lambda i: i % 2 == 0, range(11)), tuple(range(0, 11, 2))
))

test_tzip = case_of((
    lambda: tzip(['a', 'b'], range(10)), (('a', 0), ('b', 1))
))


test_flat = case_of(
    (lambda: flat([1, 2, 3]), (1, 2, 3)),
    (lambda: flat([1, 2, (3, 4)]), (1, 2, 3, 4)),
    (lambda: flat([1, 2, (3, (4, 5))]), (1, 2, 3, (4, 5))),
    (lambda: flat(tuple()), tuple()),
    (lambda: flat(str()), tuple()),


test_deep_flat = case_of(
    (lambda: deep_flat([1, 2, 3]), (1, 2, 3)),
    (lambda: deep_flat([(1, 2), 3, 4]), (1, 2, 3, 4)),
    (lambda: deep_flat([(1, [2, 3]), 4, 5]), (1, 2, 3, 4, 5)),
    (lambda: deep_flat([(1, [2, 3]), 4, 5]), (1, 2, 3, 4, 5)),
)
)
