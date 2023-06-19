from inspect import ismethod, isbuiltin, isfunction
from typing import Callable


__all__ = ("action_repr_of", )


def action_repr_of(action: Callable) -> str:
    if ismethod(action):
        return f"({action_repr_of(action.__self__)}).{action.__name__}"
    elif isbuiltin(action):
        return action.__name__
    elif isfunction(action) or isinstance(action, type):
        return action.__qualname__
    else:
        return str(action)
