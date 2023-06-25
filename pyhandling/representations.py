from inspect import ismethod, isbuiltin, isfunction
from typing import Callable


__all__ = ("code_like_repr_of", )


def code_like_repr_of(action: Callable) -> str:
    """
    Function to get a string representation of any value with priority that it
    will match the way it is given in the code.
    """

    if ismethod(action):
        return f"({code_like_repr_of(action.__self__)}).{action.__name__}"
    elif isbuiltin(action):
        return action.__name__
    elif isfunction(action) or isinstance(action, type):
        return action.__qualname__
    else:
        return str(action)
