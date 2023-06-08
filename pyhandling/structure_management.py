from collections import OrderedDict
from functools import partial
from operator import ge, le, sub, getitem, itemgetter, neg
from types import MappingProxyType
from typing import (
    Iterable, Tuple, Callable, Mapping, TypeAlias, Any, Optional, Self, Iterator
)

from pyannotating import many_or_one, Special

from pyhandling.annotations import V, M, K, action_of, checker_of, I
from pyhandling.atoming import atomically
from pyhandling.branching import then, binding_by, mergely
from pyhandling.contexting import ContextRoot, contextual
from pyhandling.data_flow import to, shown
from pyhandling.flags import flag_about
from pyhandling.operators import and_
from pyhandling.partials import rpartial, partially, rwill, will
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
    "shorten_by",
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
    "without",
    "without_duplicates",
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


def flat(collection: Iterable[Special[Iterable, V]]) -> Tuple[V]:
    """Function to expand input collection's subcollections to it."""

    collection_with_opened_items = list()

    for item in collection:
        if not isinstance(item, Iterable):
            collection_with_opened_items.append(item)
            continue

        collection_with_opened_items.extend(item)

    return tuple(collection_with_opened_items)


deep_flat: Callable[Special[Iterable, V], Tuple[V]]
deep_flat = documenting_by(
    """
    Function to expand all subcollections within an input collection while they
    exist.
    """
)(
    repeating(flat, while_=rpartial(tfilter, rpartial(isinstance, Iterable)))
)


append: Callable[..., Callable[Iterable[V] | V, Tuple[V | I]]]
append = atomically(
    tuple_of
    |then>> rwill(tuple_of)
    |then>> binding_by(as_collection |then>> ... |then>> flat)
    |then>> atomically
)


shorten_by: Callable[int, Callable[Iterable[V], Tuple[V]]]
shorten_by = atomically(
    neg
    |then>> (slice |to| None)
    |then>> itemgetter
    |then>> binding_by(tuple |then>> ...)
    |then>> atomically
)


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
        return f"[{{}}:{{}}:{{}}]".format(*map(
            on(None, str()),
            (slice_.start, slice_.stop, slice_.step),
        ))


interval = _SliceGenerator("interval")


Interval: TypeAlias = (
    int | slice | range | ContextRoot[range, Any]
    | Iterable[slice | range | ContextRoot[range, Any]]
)


def ranges_from(interval: Interval, *, border: Optional[int] = None) -> Tuple[range]:
    intervals = (
        (interval, )
        if (
            isinstance(interval, range | slice)
            or not isinstance(interval, Iterable)
        )
        else tuple(interval)
    )

    return tmap(partial(range_from, border=border), intervals)


def range_from(
    interval: int | range | slice,
    *,
    border: Optional[int] = None,
) -> range:
    if isinstance(interval, slice):
        if border is None:
            raise ValueError(
                "`border` is required to create a `range` from a `slice`"
            )

        return _range_from_slice(interval, border=border)
    elif isinstance(interval, range):
        range_ = interval
    else:
        range_ = range(interval)

    return shown(
        range(range_.start, border, range_.step)
        if range_.stop > border
        else range_
    )


def _range_from_slice(slice_: slice, *, border: int) -> range:
    start =  0 if slice_.start is None else slice_.start
    stop = 0 if slice_.stop is None else slice_.stop
    step = 1 if slice_.step is None else slice_.step

    if slice_.start is None and copysign(1, stop) != copysign(1, step):
        raise ValueError()

    if slice_.stop is None:
        stop = copysign(border, step)

    if slice_.step is None:
        step = copysign(1, stop - start)

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


def marked_ranges_from(ranges: Iterable[range]) -> Tuple[contextual[range, filled | empty]]:
    ranges = tuple(ranges)

    marked_tail_ranges = list()

    for index in range(1, len(ranges)):
        current = ranges[index]
        previous = ranges[index - 1]

        marked_tail_ranges.append(contextual(current, filled))

        if previous.stop - 1 != current.start:
            marked_tail_ranges.append(contextual(
                range(previous.stop - 1, current.start),
                empty,
            ))

    return (
        (contextual(ranges[0], filled), *marked_tail_ranges)
        if ranges
        else tuple()
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
        ranges_from(interval, border=len(values)),
    )))

    if len(ranges) > 1 or len(ranges) == 0:
        return flat(map(rpartial(to_interval, action, values), ranges))

    range_, fullness = contexted(ranges[0])

    return tuple((returned if fullness == empty else action)(values[slice_from(range_)]))


def groups_in(items: Iterable[V], id_of: action_of[V]) -> Tuple[V]:
    """
    Function of selecting groups among the elements of an input collection.
    Segregates elements by id resulting from calling the `id_of` argument.
    """

    id_by_item = from_keys(items, id_of)
    group_by_id = dict.fromkeys(id_by_item.values(), tuple())

    for item in items:
        group_by_id[id_by_item[item]] = (*group_by_id[id_by_item[item]], item)

    return tuple(group_by_id.values())


def without(
    collection: Iterable[V],
    items_or_item: many_or_one[Special[V]],
) -> Tuple[V]:
    """
    Function to get collection difference.

    The second operand can be item of a subtract collection or a subtract
    collection itself.
    """

    reduced_items = (
        tuple(items_or_item)
        if isinstance(items_or_item, Iterable)
        else (items_or_item, )
    )

    return tuple(
        item
        for item in collection
        if item not in reduced_items
    )


def without_duplicates(items: Iterable[V]) -> Tuple[V]:
    """Function to get collection without duplicates."""

    return tuple(OrderedDict.fromkeys(items).keys())


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
