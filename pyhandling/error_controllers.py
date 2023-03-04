from pyhandling.errors import PyhandingError
from pyhandling.tools import IBadResourceKeeper, DelegatingProperty, open_collection_items


class MechanicalError(PyhandingError):
    pass


class BadResourceError(MechanicalError, IBadResourceKeeper, Generic[ResourceT, ErrorT]):
    """
    Error class containing another error that occurred during the handling of
    some resource and the resource itself, respectively.
    """
    
    bad_resource = DelegatingProperty('_bad_resource')
    error = DelegatingProperty('_error')

    def __init__(self, bad_resource: ResourceT, error: ErrorT):
        self._bad_resource = bad_resource
        self._error = error

        super().__init__(
            f"Resource \"{self._bad_resource}\" could not be handled due to {type(self._error).__name__}: {str(self._error)}"
        )


@runtime_checkable
class SingleErrorKepper(Protocol, Generic[ErrorT]):
    error: ErrorT


@runtime_checkable
class ErrorKepper(Protocol, Generic[ErrorT]):
    errors: Iterable[Self | SingleErrorKepper[ErrorT] | ErrorT]


