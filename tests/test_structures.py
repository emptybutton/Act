from functools import partial

from act.testing import case_of
from act.structures import *


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
    (lambda: flat(1), (1, )),
    (lambda: flat([1, 2, 3]), (1, 2, 3)),
    (lambda: flat([1, 2, (3, 4)]), (1, 2, 3, 4)),
    (lambda: flat([1, 2, (3, (4, 5))]), (1, 2, 3, (4, 5))),
    (lambda: flat(tuple()), tuple()),
    (lambda: flat(str()), tuple()),
    (lambda: flat(item for item in [1, 2, 3]), (1, 2, 3)),
)


test_deep_flat = case_of(
    (lambda: deep_flat(1), (1, )),
    (lambda: deep_flat([1, 2, 3]), (1, 2, 3)),
    (lambda: deep_flat([(1, 2), 3, 4]), (1, 2, 3, 4)),
    (lambda: deep_flat([(1, [2, 3]), 4, 5]), (1, 2, 3, 4, 5)),
    (lambda: deep_flat([(1, [2, 3]), 4, 5]), (1, 2, 3, 4, 5)),
    (lambda: deep_flat(item for item in [1, 2, 3]), (1, 2, 3)),
)


test_append = case_of(
    (lambda: append(2)(1), (1, 2)),
    (lambda: append(3)([1, 2]), (1, 2, 3)),
    (lambda: append(3)(item for item in [1, 2]), (1, 2, 3)),
    (lambda: append(3)('ab'), ('a', 'b', 3)),
    (lambda: append([2, 3])(1), (1, [2, 3])),
    (lambda: append(None)(1), (1, None)),
    (lambda: append(2)(None), (None, 2)),
    (lambda: append(2, 3)(1), (1, 2, 3)),
)


test_without = case_of(
    (lambda: without(1)(1), tuple()),
    (lambda: without(1)((1, 2)), (2, )),
    (lambda: without(3)((1, 2)), (1, 2)),
    (lambda: without(1, 2)([1, 2]), tuple()),
    (lambda: without(1, 2)(item for item in [1, 2, 3]), (3, )),
    (lambda: without(1, 1, 1, 10)((1, 2, 1, 3, 1, 4, 1)), (2, 3, 4, 1)),
)


test_without_duplicates = case_of(
    (lambda: without_duplicates([1, 2, 2, 3, 4, 2, 3, 1]), (1, 2, 3, 4)),
    (lambda: without_duplicates((1, 2, 3, 4)), (1, 2, 3, 4)),
    (lambda: without_duplicates("banana"), ('b', 'a', 'n')),
    (lambda: without_duplicates(tuple()), tuple()),
    (lambda: without_duplicates(_ for _ in (1, 2, 1, 2, 3)), (1, 2, 3)),
)


test_slice_from = case_of(
    (lambda: slice_from(range(10)), slice(0, 10, 1)),
    (lambda: slice_from(range(2, 10)), slice(2, 10, 1)),
    (lambda: slice_from(range(2, 10, 2)), slice(2, 10, 2)),
)


test_interval = case_of(
    (lambda: tuple(interval[:10]), (slice(None, 10, None), )),
    (lambda: tuple(interval[2:10:2]), (slice(2, 10, 2), )),
    (lambda: tuple(interval[:]), (slice(None, None, None), )),
    (
        lambda: tuple(interval[2:6][-10:-2][20:15:-1]),
        (slice(2, 6, None), slice(-10, -2, None), slice(20, 15, -1)),
    ),
)


test_ranges_from = case_of(
    (lambda: ranges_from(10), (range(10, 11), )),
    (lambda: ranges_from(range(-1, -11, -1)), (range(-1, -11, -1), )),
    (lambda: ranges_from(slice(0, 10, 1)), (range(10), )),
    (lambda: ranges_from(slice(None, 10, None)), (range(10), )),
    (lambda: ranges_from(slice(None, 10, 2)), (range(0, 10, 2), )),
    (lambda: ranges_from(slice(5, 10, None)), (range(5, 10), )),
    (lambda: ranges_from(slice(5, -10, None)), (range(5, -10, -1), )),
    (lambda: ranges_from([3, 5, 10]), (range(3, 4), range(5, 6), range(10, 11))),
    (
        lambda: ranges_from([3, range(5), slice(5, None, None)], limit=7),
        (range(3, 4), range(5), range(5, 7)),
    ),
)


test_range_from = case_of(
    (lambda: range_from(10), range(10, 11)),
    (lambda: range_from(range(-1, -11, -1)), range(-1, -11, -1)),
    (lambda: range_from(range(-1, -11, -1), limit=1), range(-1, -11, -1)),
    (lambda: range_from(slice(0, 10, 1)), range(10)),
    (lambda: range_from(slice(None, 10, None)), range(10)),
    (lambda: range_from(slice(None, 10, 2)), range(0, 10, 2)),
    (lambda: range_from(slice(5, 10, None)), range(5, 10)),
    (lambda: range_from(slice(5, -10, None)), range(5, -10, -1)),
    (lambda: range_from(slice(5, None, None)), range(0, 0)),
    (lambda: range_from(slice(5, None, None), limit=3), range(0, 0)),
    (lambda: range_from(slice(5, None, -1), limit=3), range(5, -1, -1)),
)


test_marked_ranges_from = case_of(
    (lambda: marked_ranges_from([4]), (filled(range(4, 5)), )),
    (lambda: marked_ranges_from((1, 2)), (filled(range(1, 3)), )),
    (lambda: marked_ranges_from((1, 3)), (
        filled(range(1, 2)), empty(range(2, 3)), filled(range(3, 4))
    )),
    (lambda: marked_ranges_from((1, 3, 4)), (
        filled(range(1, 2)), empty(range(2, 3)), filled(range(3, 5))
    )),
    (lambda: marked_ranges_from((1, 3, 4, 9, 10, 11)), (
        filled(range(1, 2)), empty(range(2, 3)), filled(range(3, 5)),
        empty(range(5, 9)), filled(range(9, 12))
    )),
    (lambda: marked_ranges_from(range(600)), (filled(range(600)), )),
)


test_to_interval = case_of(
    (lambda: to_interval(1, partial(map, lambda v: v * 5), [1, 2, 3]), (1, 10, 3)),
    (
        lambda: to_interval(range(2), partial(map, lambda v: v * 5), [1, 2, 3]),
        (5, 10, 3),
    ),
    (
        lambda: to_interval(slice(2), partial(map, lambda v: v * 5), [1, 2, 3]),
        (5, 10, 3),
    ),
    (
        lambda: to_interval(
            range(2, 4),
            partial(map, lambda v: v * 5),
            [1, 2, 3, 4],
        ),
        (1, 2, 15, 20),
    ),
    (
        lambda: to_interval(
            [range(1), range(3, 5), range(6, 8)],
            partial(map, lambda v: v * 5),
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        ),
        (0, 1, 2, 15, 20, 5, 30, 35, 8, 9),
    ),
    (
        lambda: to_interval(
            [range(1), range(3, 5), range(6, 8)],
            partial(map, lambda v: v * 5),
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        ),
        (0, 1, 2, 15, 20, 5, 30, 35, 8, 9),
    ),
    (
        lambda: to_interval(
            [slice(1), slice(3, 5), slice(6, 8)],
            partial(map, lambda v: v * 5),
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        ),
        (0, 1, 2, 15, 20, 5, 30, 35, 8, 9),
    ),
    (
        lambda: to_interval(
            range(6),
            partial(filter, lambda v: v % 2 == 0),
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        ),
        (0, 2, 4, 6, 7, 8, 9, 10),
    ),
)


test_to_interval_via_indexer = case_of(
    (
        lambda: to_interval[2](partial(map, lambda v: v * 10), [-1, 1, 2]),
        (-1, 1, 20),
    ),
    (
        lambda: to_interval[:3][4](
            partial(map, lambda v: v * 10),
            [-1, 1, 2, 3, 4, 5],
        ),
        (-10, 10, 20, 3, 40, 5),
    ),
)


test_groups_in = case_of((
    lambda: groups_in(range(-2, 2), by=lambda v: v >= 0),
    {False: (-2, -1), True: (0, 1)},
))


test_indexed = case_of(
    (lambda: tuple(indexed([1, 2, 3], 0, 1)), ((1, 2), (2, 3))),
    (lambda: tuple(indexed([1, 2, 3, 4], 0, 1)), ((1, 2), (2, 3), (3, 4))),
)


test_table_map = case_of((
    lambda: table.map(lambda v: v * 2, dict(a=1, b=2, c=3)), dict(a=2, b=4, c=6)
))


test_table_filter = case_of((
    lambda: table.filter(lambda v: v >= 0, dict(a=-1, b=0, c=1)), dict(b=0, c=1)
))


test_table_from_keys = case_of((
    lambda: table.from_keys([1, 2, 3], str), {1: '1', 2: '2', 3: '3'}
))


test_table_reversed = case_of((
    lambda: table.reversed(dict(a=1, b=2)), {1: 'a', 2: 'b'}
))
