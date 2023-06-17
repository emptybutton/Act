from collections import OrderedDict
from functools import partial
from math import copysign
from operator import methodcaller, contains, gt, lt
from types import MappingProxyType
from typing import (
    Iterable, Tuple, Callable, Mapping, TypeAlias, Optional, Self, Iterator,
    Generator
)

from pyannotating import many_or_one, Special

from pyhandling.annotations import V, M, K, checker_of, I, Unia
from pyhandling.atomization import atomically
from pyhandling.contexting import ContextRoot, contextual, contexted
from pyhandling.data_flow import returnly, by, shown
from pyhandling.errors import RangeConstructionError, IndexingError
from pyhandling.flags import flag_about
from pyhandling.partiality import rpartial, partially, rwill
from pyhandling.pipeline import then, binding_by, ActionChain
from pyhandling.protocols import Hashable
from pyhandling.synonyms import on, tuple_of, repeating
from pyhandling.tools import documenting_by, LeftCallable


__all__ = (
    "frozendict",
    "as_collection",
    "tmap",
    "tzip",
    "tfilter",
    "flat",
    "deep_flat",
    "append",
    "without",
    "without_duplicates",
    "slice_from",
    "interval",
    "Interval",
    "ranges_from",
    "range_from",
    "disjoint_ranges_from",
    "filled",
    "empty",
    "marked_ranges_from",
    "to_interval",
    "groups_in",
    "indexed",
    "map_table",
    "filter_table",
    "from_keys",
    "reversed_table",
)


frozendict: TypeAlias = MappingProxyType


as_collection: Callable[[many_or_one[V]], Tuple[V]]
as_collection = documenting_by(
    """
    Function to convert an input value into a tuple collection.
    With a non-iterable value, wraps it in a tuple.
    """
)(
    on(rpartial(isinstance, Iterable), tuple, else_=tuple_of)
)


tmap: LeftCallable[Iterable[V], Tuple[V]]
tmap = documenting_by("""`map` function returning `tuple`""")(
    atomically(map |then>> tuple)
)


tzip: LeftCallable[Iterable[V], Tuple[V]]
tzip = documenting_by("""`zip` function returning `tuple`""")(
    atomically(zip |then>> tuple)
)


tfilter: LeftCallable[Iterable[V], Tuple[V]]
tfilter = documenting_by("""`filter` function returning `tuple`""")(
    atomically(filter |then>> tuple)
)


def flat(value: V | Iterable[Special[Iterable, V]]) -> Tuple[V]:
    """Function to expand input collection's subcollections to it."""

    collection_with_opened_items = list()

    for item in as_collection(value):
        if not isinstance(item, Iterable):
            collection_with_opened_items.append(item)
            continue

        collection_with_opened_items.extend(item)

    return tuple(collection_with_opened_items)


deep_flat: Callable[V | Special[Iterable, V], Tuple[V]]
deep_flat = documenting_by(
    """
    Function to expand all subcollections within an input collection while they
    exist.
    """
)(
    atomically(
        as_collection
        |then>> repeating(
            flat,
            while_=partial(tfilter, rpartial(isinstance, Iterable)),
        )
    )
)


append: Callable[..., Callable[Iterable[V] | V, tuple]]
append = atomically(
    tuple_of
    |then>> rwill(tuple_of)
    |then>> binding_by(as_collection |then>> ... |then>> flat)
    |then>> atomically
)


def without(*items: I) -> Callable[I | Iterable[I], Tuple[I]]:
    """
    Function for an action that represents an input value as a `tuple` with no
    items passed to this function.
    """

    removing = ActionChain(
        returnly(on(contains |by| item, methodcaller("remove", item)))
        for item in items
    )

    return atomically(as_collection |then>> list |then>> removing |then>> tuple)


def without_duplicates(items: Iterable[V]) -> Tuple[V]:
    """Function to get collection without duplicates."""

    items_without_duplicates = list()

    for item in items:
        if item not in items_without_duplicates:
            items_without_duplicates.append(item)

    return tuple(items_without_duplicates)


def slice_from(range_: range) -> slice:
    return slice(range_.start, range_.stop, range_.step)


class _SliceGenerator:
    def __init__(self, name: str, *, slices: Iterable[slice] = tuple()):
        self._name = name
        self._sleces = tuple(slices)

    def __repr__(self) -> str:
        return (
            self._name
            + str().join(map(self.__native_slice_repr_of, self._sleces))
        )

    def __getitem__(self, key: int | slice) -> Self:
        return type(self)(
            self._name,
            slices=(*self._sleces, key if isinstance(key, slice) else slice(key))
        )

    def __iter__(self) -> Iterator[slice]:
        return iter(self._sleces)

    @staticmethod
    def __native_slice_repr_of(slice_: slice) -> str:
        return "[{}:{}:{}]".format(*map(
            on(None, str()),
            (slice_.start, slice_.stop, slice_.step),
        ))


interval = _SliceGenerator("interval")


IntervalSegment: TypeAlias = int | range | slice
Interval: TypeAlias = IntervalSegment | Iterable[IntervalSegment]


def ranges_from(interval: Interval, *, limit: Optional[int] = None) -> Tuple[range]:
    intervals = (
        (interval, )
        if isinstance(interval, IntervalSegment)
        else tuple(interval)
    )

    return tmap(partial(range_from, limit=limit), intervals)


def range_from(
    interval_segment: IntervalSegment,
    *,
    limit: Optional[int] = None,
) -> range:
    if limit is not None and limit < 0:
        raise RangeConstructionError("`limit` must be greater than zero")

    if isinstance(interval_segment, slice):
        return _range_from_slice(interval_segment, limit=limit)
    elif isinstance(interval_segment, range):
        range_ = interval_segment
    else:
        range_ = range(interval_segment)

    if limit is None:
        return range_

    crosses = gt if range_.step > 0 else lt
    border = int(copysign(limit, range_.step))

    return (
        range(range_.start, border, range_.step)
        if crosses(range_.stop, border)
        else range_
    )


def _range_from_slice(slice_: slice, *, limit: Optional[int]) -> range:
    start = 0 if slice_.start is None else slice_.start
    stop = 0 if slice_.stop is None else slice_.stop
    step = 1 if slice_.step is None else slice_.step

    if slice_.start is None and copysign(1, stop) != copysign(1, step):
        raise RangeConstructionError("Unable to determine start of range")

    if slice_.stop is None:
        if limit is None:
            raise RangeConstructionError(
                "Unable to determine end of range. Set it or `limit`"
            )

        stop = int(copysign(limit, step))

    if slice_.step is None:
        step = int(copysign(1, stop - start))

    return range(start, stop, step)


def disjoint_ranges_from(numbers: Iterable[int]) -> Tuple[range]:
    numbers = sorted(set(numbers))
    ranges = list()

    last_range_start = 0

    for index, current in enumerate(numbers[:-1]):
        next_ = numbers[index + 1]

        if current + 1 != next_:
            ranges.append(last_range_start, current)
            last_range_start = next_

    return tuple(ranges)


filled = flag_about("filled")
empty = flag_about("empty")


def marked_ranges_from(
    points: Iterable[int],
) -> Tuple[contextual[range, filled | empty]]:
    points = tuple(points)

    if len(points) == 0:
        return tuple()
    elif len(points) == 1:
        return (contextual(range(points[0], points[0] + 1), filled), )
    elif len(points) == 2:
        marked_ranges = tuple()
        next_range = contextual(range(points[1], points[1] + 1), filled)
    else:
        marked_ranges = marked_ranges_from(points[1:])
        next_range = marked_ranges[0]

    fullness = filled if points[0] + 1 == points[1] else empty
    is_interval_linear = next_range.context is fullness

    return (
        (
            contextual(range(points[0], next_range.value.stop), fullness),
            *marked_ranges[1:],
        )
        if is_interval_linear
        else (contextual(range(points[0], points[1] + 1), fullness), *marked_ranges)
    )


@partially
def to_interval(
    interval: Interval,
    action: Callable[Tuple[V], Iterable[V]],
    values: Iterable[V],
) -> Tuple[V]:
    values = tuple(values)
    ranges = marked_ranges_from(disjoint_ranges_from(filter(
        and_(ge |to| 0, le |to| len(values)),
        ranges_from(interval, limit=len(values)),
    )))

    if len(ranges) > 1 or len(ranges) == 0:
        return flat(map(rpartial(to_interval, action, values), ranges))

    range_, fullness = contexted(ranges[0])

    return tuple(
        (returned if fullness == empty else action)(values[slice_from(range_)])
    )


def groups_in(
    items: Iterable[V],
    by: Callable[V, Unia[I, Hashable]],
) -> OrderedDict[Unia[I, Hashable], V]:
    """
    Function of selecting groups among the elements of an input collection.
    Segregates elements by id resulting from calling the `by` argument.
    """

    id_by_item = from_keys(items, by)
    group_by_id = OrderedDict.fromkeys(id_by_item.values(), tuple())

    for item in items:
        group_by_id[id_by_item[item]] = (*group_by_id[id_by_item[item]], item)

    return group_by_id


def indexed(items: Iterable[V], *indexes: int) -> Generator[V, None, None]:
    """Function to get ordered items under input indexes."""

    items = tuple(items)

    if any(index < 0 for index in indexes):
        raise IndexingError("indexes must be positive")

    if len(items) - max(indexes) < 0:
        raise IndexingError(
            f"there must be {max(indexes)} or more items to index",
        )

    index_border = len(items) - max(indexes)

    for current_index in range(index_border):
        yield tuple(items[current_index + index] for index in indexes)


def map_table(mapped: Callable[[V], M], table: Mapping[K, V]) -> OrderedDict[K, M]:
    """
    Function to map values of an input `Mapping` object by an input action.

    Saves sequence.
    """

    return OrderedDict((_, mapped(value)) for _, value in table.items())


def filter_table(
    is_valid: checker_of[V],
    table: Mapping[K, V],
) -> OrderedDict[K, V]:
    """
    Function to filter values of an input `Mapping` object by an input action.

    Saves sequence.
    """

    return OrderedDict((_, value) for _, value in table.items() if is_valid(value))


def from_keys(
    keys: Iterable[K],
    value_of: Callable[[K], V] = lambda _: None,
) -> OrderedDict[K, V]:
    """
    Function to create a `Mapping` with keys from an input collection and
    values obtained by applying an input action to a key under which a
    resulting value will be stored.

    Saves sequence.
    """

    return OrderedDict((key, value_of(key)) for key in keys)


def reversed_table(table: Mapping[K, V]) -> OrderedDict[V, K]:
    """
    Function to swap keys and values in `Mapping`.

    Saves sequence.
    """

    return OrderedDict(map(reversed, table.items()))
