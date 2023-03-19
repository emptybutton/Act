from functools import wraps, partial
from typing import NoReturn, Any, Iterable, Callable

from pyhandling.annotations import ResourceT, action_for, ResultT, KeyT, event_for, ContextT, ArgumentsT
from pyhandling.tools import ItemGetter, ItemSetter, ContextManager


__all__ = (
    "return_", "raise_", "assert_", "positionally_unpack_to", "unpack_by_keys_to",
    "bind", "call", "getitem_of", "setitem_of", "execute_operation", "transform",
    "to_context", "with_context_by"
)


def return_(resource: ResourceT) -> ResourceT:
    """
    Function representing the absence of an action.
    Returns the resource passed to it back.
    """

    return resource


def raise_(error: Exception) -> NoReturn:
    """Function for functional use of `raise` statement."""

    raise error


def assert_(resource: Any) -> None:
    """Function for functional use of `assert` statement."""

    assert resource


def positionally_unpack_to(func: action_for[ResultT], arguments: Iterable) -> ResultT:
    """Function for functional use of positional unpacking."""

    return func(*arguments)


def unpack_by_keys_to(func: action_for[ResultT], arguments: dict) -> ResultT:
    """Function for functional use of unpacking by keyword arguments."""

    return func(**arguments)


def bind(func: action_for[ResultT], argument_name: str, argument_value: Any) -> ResultT:
    """
    Atomic partial function for a single keyword argument whose name and value
    are separate input arguments.
    """

    return wraps(func)(partial(func, **{argument_name: argument_value}))


def call(caller: action_for[ResultT], *args, **kwargs) -> ResultT:
    """Function to call an input object and return the results of that call."""

    return caller(*args, **kwargs)


def getitem_of(object_: ItemGetter[KeyT, ResourceT], item_key: KeyT) -> ResourceT:
    """Function for functional use of `[]` getting."""

    return object_[item_key]


def setitem_of(object_: ItemSetter[KeyT, ResourceT], item_key: KeyT, item_value: ResourceT) -> None:
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