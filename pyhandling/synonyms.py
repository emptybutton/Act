from typing import Any, Callable

from pyhandling.annotations import event, handler


def return_(resource: Any) -> Any:
    """
    Wrapper function for handling emulation through the functional use of the
    return statement.
    """

    return resource


def raise_(error: Exception) -> None:
    """Wrapper function for functional use of raise statement."""

    raise error


def assert_(resource: Any) -> None:
    """Wrapper function for functional use of assert statement."""

    assert resource


def call(caller: Callable, *args, **kwargs) -> Any:
    """Function to call an input object and return the results of that call."""

    return caller(*args, **kwargs)


def call_method(object_: object, method_name: str, *args, **kwargs) -> Any:
    """Shortcut function to call a method on an input object."""

    return getattr(object_, method_name)(*args, **kwargs)


def getattr_of(object_: object, attribute_name: str) -> Any:
    """
    Synonym function for getattr.

    Unlike original getattr arguments can be keyword.
    """

    return getattr(object_, attribute_name)


def setattr_of(object_: object, attribute_name: str, attribute_value: Any) -> Any:
    """
    Synonym function for setattr.

    Unlike original setattr arguments can be keyword.
    """

    return setattr(object_, attribute_name, attribute_value)


def getitem_of(object_: object, item_key: Any) -> Any:
    """Function for functional use of [] getting."""

    return object_[item_key]


def setitem_of(object_: object, item_key: Any, item_value: Any) -> None:
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


def transform_by(operator: str, operand: Any) -> Any:
    """
    Function to use single operand operator in functional way.

    Since this function uses eval, do not pass operator from the global input to
    it.
    """

    return eval(f"{operator} operand", dict(), {'operand': operand})


def handle_context_by(context_factory: event, context_handler: handler) -> Any:
    """
    Function for emulating the "with as" context manager.

    Creates a context using the context_factory and returns the results of
    handling this context by context_handler.
    """

    with context_factory() as context:
        return context_handler(context)