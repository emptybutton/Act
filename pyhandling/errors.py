from typing import Any

from pyhandling.tools import IBadResource, DelegatingProperty


class PyhandingError(Exception):
    pass


class HandlingRecursionError(PyhandingError):
    pass


class HandlingRecursionDepthError(HandlingRecursionError):
    __notes__ = ("To change the limit, call recursive with the max_recursion_depth argument, with the desired value", )


class BadResourceError(PyhandingError, IBadResource):
    """
    Error class containing another error that occurred during the handling of
    some resource and the resource itself, respectively.
    """
    
    resource = DelegatingProperty('_resource')
    error = DelegatingProperty('_error')

    def __init__(self, resource: Any, error: Exception):
        self._resource = resource
        self._error = error

        super().__init__(
            f"Resource \"{self.resource}\" could not be handled due to {type(self.error).__name__}: {str(self.error)}"
        )