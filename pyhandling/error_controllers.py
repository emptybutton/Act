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


error_storage_of = partial(AnnotationTemplate, Union)(
    AnnotationTemplate(ErrorKepper, [input_annotation]),
    AnnotationTemplate(SingleErrorKepper, [input_annotation]),
    input_annotation
)


def errors_from(error_storage: error_storage_of[ErrorT]) -> Tuple[ErrorT]:
    """
    Function to recursively get all (including nested) errors from unstructured
    error storage.
    """

    errors = (error_storage, ) if isinstance(error_storage, Exception) else tuple()

    if isinstance(error_storage, SingleErrorKepper):
        errors += errors_from(error_storage.error)
    if isinstance(error_storage, ErrorKepper):
        errors += open_collection_items(map(errors_from, error_storage.errors))

    return errors


@runtime_checkable
class ErrorReport(Protocol, Generic[ErrorT]):
    """Protocol for saving error context as a document."""

    error: ErrorT
    document: Mapping


class ReportingError(MechanicalError, Generic[ErrorT]):
    """Error class to store the context of another error and itself."""
    
    document = DelegatingProperty("_document")

    def __init__(self, error: ErrorT, document: Mapping):
        self.__error = error
        self.__document = MappingProxyType(document)

        super().__init__(self._error_message)

    @cached_property
    def _error_message(self) -> str:
        formatted_report = format_dict(self.__document, line_between_key_and_value='=')

        return (
            str(self.__error)
            + (" when {formatted_document}" if self.__document else str())
        )