from functools import reduce
from typing import Iterable

from pyhandling.collections_ import NonInclusiveCollection, MultiRange

from pytest import mark, fail


@mark.parametrize(
    'elements_not_included, elements_included',
    (
        (range(10), range(10, 20)),
        (range(-10, 0), range(3)),
        (range(-100, 50), range(100, 150))
    )
)
def test_non_inclusive_collection(elements_not_included: Iterable, elements_included: Iterable):
    non_inclusive_collection = NonInclusiveCollection(elements_not_included)

    if not tuple(elements_not_included):
        fail('elements_not_included are empty')

    if not tuple(elements_included):
        fail('elements_included are empty')

    if set(elements_not_included) & set(elements_included):
        fail('elements_included and elements_not_included are cross')

    assert all(
        element_not_included not in non_inclusive_collection
        for element_not_included in elements_not_included
    ) and all(
        element_included in non_inclusive_collection
        for element_included in elements_included
    )


@mark.parametrize(
    'ranges',
    [(range(10), range(-10, -3), range(100, 120), range(55, 65), range(256, 260))]
)
def test_multi_range_elements(ranges: Iterable[range]):
    assert (
        reduce(lambda first, second: set(first) | set(second), ranges)
        == set(MultiRange(ranges))
    )


@mark.parametrize(
    'first_ranges, second_ranges',
    [(
        (range(3, 6), range(9, 12), range(500, 510)),
        (range(-100, -50), range(-25, 10), range(1000, 1001))
    )]
)
def test_multi_range_union_with_other(first_ranges: Iterable[range], second_ranges: Iterable[range]):
    assert (
        set(MultiRange(first_ranges) | MultiRange(second_ranges))
        == set(MultiRange(tuple(first_ranges) + tuple(second_ranges)))
    )


@mark.parametrize(
    'first_ranges, second_range_resource',
    [
        (
            (range(3, 6), range(9, 12), range(500, 510)),
            (range(-100, -50), range(-25, 10), range(1000, 1001))
        ),
        (
            (range(55, 60), range(62, 65), range(10)),
            range(-100, 0)
        )
    ]
)
def test_multi_range_union_with_ranges(first_ranges: Iterable[range], second_range_resource: Iterable[range] | range):
    assert (
        set(MultiRange(first_ranges) | second_range_resource)
        == set(MultiRange(
            tuple(first_ranges) + (
                (second_range_resource, )
                if isinstance(second_range_resource, range)
                else tuple(second_range_resource)
            )
        ))
    )