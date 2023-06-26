from inspect import ismethod, isbuiltin, isfunction
from typing import Any


__all__ = ("code_like_repr_of", )


def code_like_repr_of(value: Any) -> str:
    """
    Function to get a string representation of any value with priority that it
    will match the way it is given in the code.
    """

    if ismethod(value):
        return f"({code_like_repr_of(value.__self__)}).{value.__name__}"
    elif isbuiltin(value):
        return value.__name__
    elif isfunction(value) or isinstance(value, type):
        return value.__qualname__
    else:
        return str(value)
