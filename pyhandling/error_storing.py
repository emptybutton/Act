from abc import ABC, abstractmethod
from functools import cached_property
from types import MappingProxyType
from typing import Generic, Union, runtime_checkable, Protocol, Iterable, Self, Tuple, NamedTuple, Optional, ClassVar, Iterator

from pyannotating import Special, AnnotationTemplate, input_annotation

from pyhandling.annotations import ErrorT, ContextT
from pyhandling.errors import PyhandingError
from pyhandling.language import to
from pyhandling.immutability import property_of
from pyhandling.structure_management import with_opened_items


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
class SingleErrorKepper(Protocol, Generic[ErrorT]):
    error: ErrorT | Self | "ErrorKepper"


@runtime_checkable
class ErrorKepper(Protocol, Generic[ErrorT]):
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
        errors += with_opened_items(map(errors_from, error_storage.errors))

    return errors
