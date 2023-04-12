from inspect import stack
from typing import Any


__all__ = ("value_of", )


def value_of(__variable_name: str) -> Any:
    __frame = stack()[1][0]

    while __variable_name not in __frame.f_locals:
        __frame = __frame.f_back

        if __frame is None:
            return eval(__variable_name)

    return __frame.f_locals[__variable_name]