from abc import ABC, abstractmethod
from functools import update_wrapper
from inspect import Signature, signature, _empty
from typing import Generic, Callable, Any, Union

from pyannotating import Special

from pyhandling.annotations import ActionT


__all__ = ("ActionWrapper", "calling_signature_of", "annotation_sum")


class ActionWrapper(ABC, Generic[ActionT]):
    def __init__(self, action: ActionT):
        self._action = action
        self._become_native()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._action})"

    @property
    @abstractmethod
    def _force_signature(self) -> Signature:
        ...

    def _become_native(self) -> None:
        update_wrapper(self, self._action)
        self.__signature__ = self._force_signature


def calling_signature_of(action: Callable) -> Signature:
    try:
        return signature(action)
    except ValueError:
        return signature(lambda *args, **kwargs: ...)


def annotation_sum(*args: Special[_empty]) -> Any:
    annotations = tuple(arg for arg in args if arg is not _empty)

    return Union[*annotations] if annotations else _empty
