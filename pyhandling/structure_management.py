from collections import OrderedDict
from typing import Iterable, Tuple, Callable, Mapping

from pyannotating import many_or_one

from pyhandling.annotations import ValueT, MappedT, KeyT, ValueT, action_of
from pyhandling.atoming import atomically
from pyhandling.branching import on
from pyhandling.language import by, then
from pyhandling.tools import documenting_by


__all__ = (
    "in_collection",
    "with_opened_items",
    "as_collection",
    "tmap",
    "tzip",
    "tfilter",
    "groups_in",
    "table_value_map",
    "from_keys",
    "reversed_table",
)


def in_collection(value: ValueT) -> tuple[ValueT]:
    """Function to represent the input value as a single collection."""

    return (value, )


def with_opened_items(collection: Iterable) -> Tuple:
    """Function to expand input collection's subcollections to it."""

    collection_with_opened_items = list()

    for item in collection:
        if not isinstance(item, Iterable):
            collection_with_opened_items.append(item)
            continue

        collection_with_opened_items.extend(item)

    return tuple(collection_with_opened_items)


as_collection: Callable[[many_or_one[ValueT]], Tuple[ValueT]]
as_collection = documenting_by(
    """
    Function to convert an input value into a tuple collection.
    With a non-iterable value, wraps it in a tuple.
    """
)(
    on(isinstance |by| Iterable, tuple, else_=in_collection)
)


tmap = documenting_by("""`map` function returning `tuple`""")(
    atomically(map |then>> tuple)
)


tzip = documenting_by("""`zip` function returning `tuple`""")(
    atomically(zip |then>> tuple)
)


tfilter = documenting_by("""`filter` function returning `tuple`""")(
    atomically(filter |then>> tuple)
)


def groups_in(items: Iterable[ValueT], id_of: action_of[ValueT]) -> Tuple[ValueT]:
    id_by_item = from_keys(items, id_of)
    group_by_id = dict.fromkeys(id_by_item.values(), tuple())

    for item in items:
        group_by_id[id_by_item[item]] = (*group_by_id[id_by_item[item]], item)

    return tuple(group_by_id.values())


def table_value_map(
    mapped: Callable[[ValueT], MappedT],
    table: Mapping[KeyT, ValueT],
) -> OrderedDict[KeyT, MappedT]:
    return OrderedDict((_, mapped(value)) for _, value in table.items())


def from_keys(
    keys: Iterable[KeyT],
    value_of: Callable[[KeyT], ValueT] = lambda _: None,
) -> OrderedDict[KeyT, ValueT]:
    return OrderedDict((key, value_of(key)) for key in keys)


def reversed_table(table: Mapping[KeyT, ValueT]) -> OrderedDict[ValueT, KeyT]:
    return OrderedDict(map(reversed, table.items()))
