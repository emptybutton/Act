from abc import ABC, abstractmethod
from functools import cached_property
from types import MappingProxyType
from typing import Generic, Union, runtime_checkable, Protocol, Iterable, Self, Tuple, TypeVar, NamedTuple

from pyannotating import AnnotationTemplate, input_annotation

from pyhandling.annotations import ResourceT, ErrorT, ResultT
from pyhandling.errors import PyhandingError
from pyhandling.language import to
from pyhandling.tools import DelegatingProperty, open_collection_items


__all__ = (
    "MechanicalError", "IBadResourceKeeper", "BadResourceWrapper",
    "bad_wrapped_or_not", "BadResourceError", "SingleErrorKepper", "ErrorKepper",
    "error_storage_of", "errors_from", "ContextT", "ErrorReport",
    "ContextualError", "ResultWithError"
)


class MechanicalError(PyhandingError):
    pass


class IBadResourceKeeper(ABC, Generic[ResourceT]):
    """Class for annotating a resource that is invalid under some circumstances."""

    @property
    @abstractmethod
    def bad_resource(self) -> ResourceT:
        pass


class BadResourceWrapper(IBadResourceKeeper, Generic[ResourceT]):
    """
    Implementation class for the BadResourceKeeper interface for storing a
    resource without the context of its badness.
    """

    bad_resource = DelegatingProperty('_bad_resource')

    def __init__(self, resource: ResourceT):
        self._bad_resource = resource

    def __repr__(self) -> str:
        return f"<Wrapper of bad {self.bad_resource}>"


bad_wrapped_or_not = (AnnotationTemplate |to| Union)([
    AnnotationTemplate(BadResourceWrapper, [input_annotation]),
    input_annotation
])


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


error_storage_of = (AnnotationTemplate |to| Union)([
    AnnotationTemplate(ErrorKepper, [input_annotation]),
    AnnotationTemplate(SingleErrorKepper, [input_annotation]),
    input_annotation
])


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


ContextT = TypeVar("ContextT")


@runtime_checkable
class ErrorReport(Protocol, Generic[ErrorT, ContextT]):
    """Protocol for saving error context."""

    error: ErrorT
    context: ContextT


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


class ResultWithError(NamedTuple, Generic[ResultT, ErrorT]):
    """Named tuple storing someone's possible result or error."""

    result: Optional[ResultT]
    error: Optional[ErrorT]