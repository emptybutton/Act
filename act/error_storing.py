from typing import Union, runtime_checkable, Protocol, Self, Tuple, Iterable

from pyannotating import AnnotationTemplate, input_annotation

from act.annotations import ErrorT
from act.errors import PyhandingError
from act.structures import flat


__all__ = (
    "MechanicalError",
    "SingleErrorKepper",
    "ErrorKepper",
    "error_storage_of",
    "errors_from",
)


class MechanicalError(PyhandingError):
    pass


@runtime_checkable
class SingleErrorKepper(Protocol[ErrorT]):
    error: ErrorT | Self | "ErrorKepper"


@runtime_checkable
class ErrorKepper(Protocol[ErrorT]):
    errors: Iterable[Self | SingleErrorKepper[ErrorT] | ErrorT]


error_storage_of = AnnotationTemplate(Union, [
    AnnotationTemplate(ErrorKepper, [input_annotation]),
    AnnotationTemplate(SingleErrorKepper, [input_annotation])
])


def errors_from(error_storage: error_storage_of[ErrorT] | ErrorT) -> Tuple[ErrorT]:
    """
    Function to recursively get all (including nested) errors from unstructured
    error storage (and storage itself, if it is also an error).
    """

    errors = (error_storage, ) if isinstance(error_storage, Exception) else tuple()

    if isinstance(error_storage, SingleErrorKepper):
        errors += errors_from(error_storage.error)
    if isinstance(error_storage, ErrorKepper):
        errors += flat(map(errors_from, error_storage.errors))

    return errors
