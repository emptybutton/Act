from functools import wraps, partial
from typing import NoReturn, Any, Iterable, Callable, Mapping

from pyhandling.annotations import ValueT, action_for, ResultT, KeyT, event_for, ContextT, ArgumentsT
from pyhandling.protocols import ItemGetter, ItemSetter, ContextManager


__all__ = (
    "returned", "raise_", "assert_", "collection_of", "with_positional_unpacking",
    "with_keyword_unpacking", "with_keyword", "call", "getitem", "setitem",
    "execute_operation", "transform", "to_context", "with_context_by"
)


def returned(value: ValueT) -> ValueT:
    """
    Function representing the absence of an action.
    Returns the value passed to it back.
    """

    return value


def raise_(error: Exception) -> NoReturn:
    """Function for functional use of `raise` statement."""

    raise error


def assert_(value: Any) -> None:
    """Function for functional use of `assert` statement."""

    assert value


def collection_of(*args) -> tuple:
    """Function to create a `tuple` from unlimited input arguments."""

    return args


def with_positional_unpacking(func: action_for[ResultT]) -> Callable[[Iterable], ResultT]:
    """Function for functional use of positional unpacking."""

    return wraps(func)(lambda arguments: func(*arguments))


    """Function for functional use of unpacking by keyword arguments."""
def with_keyword_unpacking(func: action_for[ResultT]) -> Callable[[Mapping[str, Any]], ResultT]:

    return wraps(func)(lambda arguments: func(**arguments))


def with_keyword(argument_name: str, argument_value: Any, func: action_for[ResultT]) -> ResultT:
    """
    Atomic partial function for a single keyword argument whose name and value
    are separate input arguments.
    """

    return wraps(func)(partial(func, **{argument_name: argument_value}))


def call(caller: action_for[ResultT], *args, **kwargs) -> ResultT:
    """Function to call an input object and return the results of that call."""

    return caller(*args, **kwargs)


def getitem(object_: ItemGetter[KeyT, ValueT], item_key: KeyT) -> ValueT:
    """Function for functional use of `[]` getting."""

    return object_[item_key]


def setitem(object_: ItemSetter[KeyT, ValueT], item_key: KeyT, item_value: ValueT) -> None:
    """Function for functional use of `[]` setting."""

    object_[item_key] = item_value


def execute_operation(first_operand: Any, operator: str, second_operand: Any) -> Any:
    """
    Function to use operators.

    Since this function uses `eval`, do not pass `operator` from the global
    input to it.
    """

    return eval(
        f"first_operand {operator} second_operand",
        dict(),
        {'first_operand': first_operand, 'second_operand': second_operand}
    )


def transform(operand: Any, operator: str) -> Any:
    """
    Function to use single operand operator.

    Since this function uses `eval`, do not pass `operator` from the global
    input to it.
    """

    return eval(f"{operator} operand", dict(), {'operand': operand})


def to_context(action: Callable[[ContextT], ResultT]) -> Callable[[ContextManager[ContextT]], ResultT]:
    """Function emulating the `with as` context manager."""

    @wraps(action)
    def contextual_action(context_manager: ContextManager[ContextT]) -> ResultT:
        with context_manager as context:
            return action(context)

    return contextual_action


def with_context_by(
    get_context: Callable[[*ArgumentsT], ContextManager[ContextT]],
    action: Callable[[*ArgumentsT], ResultT]
) -> Callable[[*ArgumentsT], ResultT]:
    """Function to perform an input action in a specific context."""

    @wraps(action)
    def contextual_action(*args, **kwargs) -> Any:
        with get_context(*args, **kwargs):
            return action(*args, **kwargs)


    return contextual_action