from inspect import stack
from typing import Any


__all__ = ("value_of", )


def value_of(variable_name: str) -> Any:
    frame = stack()[1][0]

    while variable_name not in frame.f_locals:
        frame = frame.f_back

        if frame is None:
            return eval(variable_name)

    return frame.f_locals[variable_name]