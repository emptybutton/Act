from collections import OrderedDict
from typing import Iterable, Tuple, Callable, Mapping

from pyannotating import many_or_one

from pyhandling.annotations import ValueT, MappedT, KeyT, ValueT
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
    "table_value_map",
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


def table_value_map(
    mapped: Callable[[ValueT], MappedT],
    table: Mapping[KeyT, ValueT],
) -> OrderedDict[KeyT, MappedT]:
    return OrderedDict((_, mapped(value)) for _, value in table.items())


def reversed_table(table: Mapping[KeyT, ValueT]) -> OrderedDict[ValueT, KeyT]:
    return OrderedDict(map(reversed, table.items()))
