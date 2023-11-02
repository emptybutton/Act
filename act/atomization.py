from dataclasses import dataclass
from functools import update_wrapper
from typing import runtime_checkable, Protocol, Self, Callable, Generic, TypeAlias

from act.annotations import AtomizableT, Pm, R
from act.errors import AtomizationError
from act.representations import code_like_repr_of


__all__ = ("Atomizable", "atomic", "fun")


@runtime_checkable
class Atomizable(Protocol):
    """
    Protocol for objects capable of being converted to atomic form.

    The `atomic` function is used to convert.
    """

    def __getatom__(self) -> Self:
        ...


def atomic(value: AtomizableT) -> AtomizableT:
    """
    Function representing an input object in its atomic form.

    Is a public synonym for calling the `__getatom__` method.
    """

    if not isinstance(value, Atomizable):
        raise AtomizationError(f"{type(value).__name__} object is not atomizable'")

    return value.__getatom__()


class fun:
    """
    Decorator that removes the behavior of an input action, leaving only
    calling.
    """

    @dataclass(frozen=True)
    class Image(Generic[Pm, R]):
        action: Callable[Pm, R]
        get_represented: Callable[[], str]

    @runtime_checkable
    class Imagenariable(Protocol[Pm, R]):
        def __fun_image__(self) -> "fun.Image[Pm, R]":
            ...

    _ImageValue: TypeAlias = Image[Pm, R] | Imagenariable[Pm, R] | Callable[Pm, R]

    def __init__(self, value: _ImageValue) -> None:
        self._image = self.__image_by(value)
        update_wrapper(self, self._image.action)

    def __repr__(self) -> str:
        return f"fun({self._image.get_represented()})"

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._image.action(*args, **kwargs)

    def __image_by(self, value: _ImageValue) -> Image:
        if isinstance(value, fun.Image):
            return value
        elif isinstance(value, fun.Imagenariable):
            return value.__fun_image__()
        else:
            return fun.Image(value, lambda: code_like_repr_of(value))
