from typing import Any

from pyhandling.tools import IBadResourceKeeper, DelegatingProperty
class PyhandingError(Exception):
    pass


class NeutralActionChainError(PyhandingError):
    pass


class HandlingRecursionError(PyhandingError):
    pass


class HandlingRecursionDepthError(HandlingRecursionError):
    __notes__ = [
        "To change the limit, call recursive with the max_recursion_depth argument, with the desired value"
    ]


class BadResourceError(PyhandingError, IBadResourceKeeper):
    """
    Error class containing another error that occurred during the handling of
    some resource and the resource itself, respectively.
    """
    
    bad_resource = DelegatingProperty('_bad_resource')
    error = DelegatingProperty('_error')

    def __init__(self, bad_resource: Any, error: Exception):
        self._bad_resource = bad_resource
        self._error = error

        super().__init__(
            f"Resource \"{self._bad_resource}\" could not be handled due to {type(self._error).__name__}: {str(self._error)}"
        )