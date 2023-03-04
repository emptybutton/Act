from functools import wraps, partial
from typing import Any, Callable, Iterable

from pyhandling.annotations import event, handler


def return_(resource: ResourceT) -> ResourceT:
    """
    Wrapper function for handling emulation through the functional use of the
    return statement.
    """

    return resource


def raise_(error: Exception) -> NoReturn:
    """Wrapper function for functional use of raise statement."""

    raise error


def assert_(resource: Any) -> None:
    """Wrapper function for functional use of assert statement."""

    assert resource


def positionally_unpack_to(func: event_for[ResultT], arguments: Iterable) -> ResultT:
    """Wrapper function for functional use of positional unpacking."""

    return func(*arguments)


def unpack_by_keys_to(func: event_for[ResultT], arguments: dict) -> ResultT:
    """Wrapper function for functional use of unpacking by keyword arguments."""

    return func(**arguments)


def bind(func: event_for[ResultT], argument_name: str, argument_value: Any) -> ResultT:
    """
    Atomic partial function for a single keyword argument whose name and value
    are separate input arguments.
    """

    return wraps(func)(partial(func, **{argument_name: argument_value}))


def call(caller: event_for[ResultT], *args, **kwargs) -> ResultT:
    """Function to call an input object and return the results of that call."""

    return caller(*args, **kwargs)


def getitem_of(object_: ItemGetter[KeyT, ResourceT], item_key: KeyT) -> ResourceT:
    """Function for functional use of [] getting."""

    return object_[item_key]


def setitem_of(object_: ItemSetter[KeyT, ResourceT], item_key: KeyT, item_value: ResourceT) -> None:
    """Function for functional use of [] setting."""

    object_[item_key] = item_value


def execute_operation(first_operand: Any, operator: str, second_operand: Any) -> Any:
    """
    Function to use python operators in a functional way.

    Since this function uses eval, do not pass operator and unchecked standard
    type operands from the global input to it.
    """

    return eval(
        f"first_operand {operator} second_operand",
        dict(),
        {'first_operand': first_operand, 'second_operand': second_operand}
    )


def transform(operand: Any, operator: str) -> Any:
    """
    Function to use single operand operator in functional way.

    Since this function uses eval, do not pass operator from the global input to
    it.
    """

    return eval(f"{operator} operand", dict(), {'operand': operand})


def handle_context_by(context_factory: event, context_handler: Callable[[Any], ResultT]) -> ResultT:
    """
    Function for emulating the "with as" context manager.

    Creates a context using the context_factory and returns the results of
    handling this context by context_handler.
    """

    with context_factory() as context:
        return context_handler(context)