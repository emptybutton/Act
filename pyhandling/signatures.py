from abc import ABC, abstractmethod
from inspect import Signature, signature, Parameter, getdoc
from typing import Generic, Callable, Any, Union

from pyannotating import Special

from pyhandling.annotations import ActionT
from pyhandling.representations import code_like_repr_of
from pyhandling.tools import LeftCallable


__all__ = ("Decorator", "call_signature_of", "annotation_sum")


class Decorator(LeftCallable, ABC, Generic[ActionT]):
    """
    Abstract class for decorating an input action and creating a signature
    based on it.

    Set signature from `_force_signature` attribute.

    When `_doc_parser = True` assigns itself an input action documentation.
    """

    _doc_parser: bool = False

    def __init__(self, action: ActionT):
        self._action = action
        self._become_native()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({code_like_repr_of(self._action)})"

    @property
    @abstractmethod
    def _force_signature(self) -> Signature:
        ...

    def _become_native(self) -> None:
        """Method editing an instance for a decorated action."""

        self.__signature__ = self._force_signature

        if self._doc_parser:
            doc = getdoc(self._action)
            self.__doc__ = str() if doc is None else doc


def call_signature_of(action: Callable) -> Signature:
    """
    Function to get input action signature.
    If there is no signature, returns an undefined signature.
    """

    try:
        return signature(action)
    except ValueError:
        return signature(lambda *args, **kwargs: ...)


def annotation_sum(*args: Special[Parameter.empty]) -> Any:
    """Function to create `Union` given `Parameter.empty`."""

    annotations = tuple(arg for arg in args if arg is not Parameter.empty)

    return Union[*annotations] if annotations else Parameter.empty
