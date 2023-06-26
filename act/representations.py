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
    elif isinstance(value, slice):
        return "{}:{}{}".format(
            str() if value.start is None else value.start,
            str() if value.stop is None else value.stop,
            str() if value.step in (None, 1) else f":{value.step}",
        )
    else:
        return str(value)
