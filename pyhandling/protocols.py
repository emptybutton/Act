from typing import runtime_checkable, Protocol, Generic, Any, Optional, Type

from pyhandling.annotations import KeyT, ResultT, ValueT, ContextT


__all__ = (
    "ItemGetter",
    "ItemSetter",
    "ItemKeeper",
    "ContextManager",
    "Variable",
)


@runtime_checkable
class ItemGetter(Protocol, Generic[KeyT, ResultT]):
    """
    Protocol describing objects from which it is possible to get a value by
    accessing via `[]` (`item_getter[key]`).
    """

    def __getitem__(self, key: KeyT) -> ResultT:
        ...


@runtime_checkable
class ItemSetter(Protocol, Generic[KeyT, ValueT]):
    """
    Protocol describing objects from which it is possible to set a value by
    accessing via `[]` (`item_setter[key] = value`).
    """

    def __setitem__(self, key: KeyT, value: ValueT) -> Any:
        ...


@runtime_checkable
class ItemKeeper(ItemGetter, ItemSetter, Protocol, Generic[KeyT, ValueT]):
    """
    Protocol describing objects from which it is possible to get the value via
    `[]` access and write the value via the same `[]` access.

    In the form
    ```
    item_keeper[key]
    item_keeper[key] = value
    ```
    """


@runtime_checkable
class ContextManager(Protocol, Generic[ContextT]):
    """
    Protocol describing objects managing a context via the syntactic
    `with ... as ...` construct.
    """

    def __enter__(self) -> ContextT:
        ...

    def __exit__(
        self,
        error_type: Optional[Type[Exception]],
        error: Optional[Exception],
        traceback: Any,
    ):
        ...


@runtime_checkable
class Variable(Protocol):
    """
    Protocol describing objects capable of checking another object against a
    subvariant of the describing object (`isinstance(another, describing)`).
    """

    def __instancecheck__(self, instance: object) -> bool:
        ...