from collections import OrderedDict
from types import MappingProxyType
from typing import Iterable, Tuple, Callable, Mapping, TypeAlias

from pyannotating import many_or_one, Special

from pyhandling.annotations import ValueT, MappedT, KeyT, action_of
from pyhandling.atoming import atomically
from pyhandling.data_flow import by
from pyhandling.branching import then
from pyhandling.synonyms import on
from pyhandling.tools import documenting_by


__all__ = (
    "frozendict",
    "in_collection",
    "with_opened_items",
    "as_collection",
    "tmap",
    "tzip",
    "tfilter",
    "groups_in",
    "without",
    "table_map",
    "table_filter",
    "from_keys",
    "reversed_table",
    "dict_of",
)


frozendict: TypeAlias = MappingProxyType


def in_collection(value: ValueT) -> tuple[ValueT]:
    """Function to represent the input value in a single collection."""

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
    collection: Iterable[ValueT],
    items_or_item: Iterable[ValueT] | ValueT,
) -> Tuple[ValueT]:
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


def map_table(
    mapped: Callable[[ValueT], MappedT],
    table: Mapping[KeyT, ValueT],
) -> OrderedDict[KeyT, MappedT]:
    """
    Function to map values of an input `Mapping` object by an input action.

    Saves sequence.
    """

    return OrderedDict((_, mapped(value)) for _, value in table.items())


def filter_table(
    is_valid: checker_of[ValueT],
    table: Mapping[KeyT, ValueT],
) -> OrderedDict[KeyT, ValueT]:
    """
    Function to filter values of an input `Mapping` object by an input action.

    Saves sequence.
    """

    return OrderedDict((_, value) for _, value in table.items() if is_valid(value))


def from_keys(
    keys: Iterable[KeyT],
    value_of: Callable[[KeyT], ValueT] = lambda _: None,
) -> OrderedDict[KeyT, ValueT]:
    """
    Function to create a `Mapping` with keys from an input collection and
    values obtained by applying an input action to a key under which a
    resulting value will be stored.

    Saves sequence.
    """

    return OrderedDict((key, value_of(key)) for key in keys)


def reversed_table(table: Mapping[KeyT, ValueT]) -> OrderedDict[ValueT, KeyT]:
    """
    Function to swap keys and values in `Mapping`.

    Saves sequence.
    """

    return OrderedDict(map(reversed, table.items()))


def dict_of(value: Special[Mapping[KeyT, ValueT]]) -> dict[KeyT, ValueT]:
    """
    Function converting input value to `dict`.

    When passing a `Mapping` object, cast it to a `dict`, otherwise return
    `__dict__` of an input object.
    """

    return dict(**value) if isinstance(value, Mapping) else value.__dict__
