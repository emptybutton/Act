from inspect import Signature, signature
from typing import Callable


__all__ = ("call_signature_of", )


def call_signature_of(action: Callable) -> Signature:
    """
    Function to get input action signature.
    If there is no signature, returns an undefined signature.
    """

    try:
        return signature(action)
    except ValueError:
        return signature(lambda *args, **kwargs: ...)
