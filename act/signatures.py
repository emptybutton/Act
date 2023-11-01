from inspect import Signature, signature, Parameter
from typing import Callable, Any, Union

from pyannotating import Special


__all__ = ("call_signature_of", "annotation_sum")


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
