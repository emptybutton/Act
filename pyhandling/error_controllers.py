from abc import ABC, abstractmethod
from functools import cached_property
from types import MappingProxyType
from typing import Generic, Union, runtime_checkable, Protocol, Iterable, Self, Tuple, NamedTuple, Optional

from pyannotating import AnnotationTemplate, input_annotation

from pyhandling.annotations import ResourceT, ErrorT, ContextT
from pyhandling.errors import PyhandingError
from pyhandling.language import to
from pyhandling.tools import DelegatingProperty, with_opened_items


__all__ = (
    "MechanicalError", "SingleErrorKepper", "ErrorKepper", "error_storage_of",
    "errors_from", "ErrorReport", "ContextualError"
)


class MechanicalError(PyhandingError):
    pass


@runtime_checkable
class SingleErrorKepper(Protocol, Generic[ErrorT]):
    error: ErrorT | Self | "ErrorKepper"


@runtime_checkable
class ErrorKepper(Protocol, Generic[ErrorT]):
    errors: Iterable[Self | SingleErrorKepper[ErrorT] | ErrorT]


error_storage_of = (AnnotationTemplate |to| Union)([
    AnnotationTemplate(ErrorKepper, [input_annotation]),
    AnnotationTemplate(SingleErrorKepper, [input_annotation])
])


def errors_from(error_storage: error_storage_of[ErrorT] | ErrorT) -> Tuple[ErrorT]:
    """
    Function to recursively get all (including nested) errors from unstructured
    error storage.
    """

    errors = (error_storage, ) if isinstance(error_storage, Exception) else tuple()

    if isinstance(error_storage, SingleErrorKepper):
        errors += errors_from(error_storage.error)
    if isinstance(error_storage, ErrorKepper):
        errors += with_opened_items(map(errors_from, error_storage.errors))

    return errors


class ContextualError(MechanicalError, Generic[ErrorT, ContextT]):
    """Error class to store the context of another error and itself."""
   
    error = DelegatingProperty("__error")
    context = DelegatingProperty("__context")

    def __init__(self, error: ErrorT, context: ContextT):
        self.__error = error
        self.__context = context

        super().__init__(self._error_message)

    @cached_property
    def _error_message(self) -> str:
        return f"{str(self.__error)} in context {self.__context}"