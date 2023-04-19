from abc import ABC, abstractmethod
from functools import partial, reduce
from typing import Generic, Callable, Optional, Iterable, Any, Self

from pyannotating import Special

from pyhandling.annotations import ResultT, ValueT, P
from pyhandling.atoming import atomically
from pyhandling.data_flow import eventually
from pyhandling.branching import ActionChain
from pyhandling.immutability import property_to
from pyhandling.partials import rpartial, will
from pyhandling.synonyms import returned
from pyhandling.tools import documenting_by


__all__ = ("PartialApplicationInfix", "then", "to", "by")


class PartialApplicationInfix(ABC):
    """
    Infix class for action partial application.

    Used in the form `action |instance| argument` or `action |instance* arguments`
    if you want to unpack the arguments.
    """

    @abstractmethod
    def __or__(self, argument: Any) -> Callable:
        ...

    @abstractmethod
    def __ror__(self, action_to_transform: Callable) -> Self | Callable:
        ...

    @abstractmethod
    def __mul__(self, arguments: Iterable) -> Callable:
        ...


class _CustomPartialApplicationInfix(PartialApplicationInfix):
    """
    Infix class for binding functions with arguments.

    Used in the form `func |instance| argument` or `func |instance* arguments`
    if you want to unpack the arguments.
    """

    def __init__(
        self,
        transform: Callable[[Callable, ValueT], Callable],
        *,
        action_to_transform: Optional[Callable] = None,
        arguments: Optional[Iterable[ValueT]] = None
    ):
        self._transform = transform
        self._action_to_transform = action_to_transform
        self._arguments = arguments

    def __repr__(self) -> str:
        return "PartialApplicationInfix for {}".format(
            self._transform.__name__
            if hasattr(self._transform, '__name__')
            else self._transform
        )

    def __or__(self, argument: Any) -> Callable:
        return self._transform(self._action_to_transform, argument)

    def __ror__(self, action_to_transform: Callable) -> Self | Callable:
        return (
            type(self)(self._transform, action_to_transform=action_to_transform)
            if self._arguments is None
            else reduce(self._transform, (action_to_transform, *self._arguments))
        )

    def __mul__(self, arguments: Iterable) -> Callable:
        return type(self)(self._transform, arguments=arguments)


class _CallableCustomPartialApplicationInfix(_CustomPartialApplicationInfix):
    def __init__(
        self,
        transform: Callable[[Callable, ValueT], Callable],
        *,
        action_to_call: Callable[P, ResultT] = returned,
        action_to_transform: Optional[Callable] = None,
        arguments: Optional[Iterable[ValueT]] = None,
    ):
        super().__init__(
            transform,
            action_to_transform=action_to_transform,
            arguments=arguments,
        )
        self._action_to_call = action_to_call

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self._action_to_call(*args, **kwargs)


then = documenting_by(
    """
    Neutral instance of `ActionChain`.

    Used as a pseudo-operator to build an `ActionChain` and, accordingly,
    combine calls of several functions in a pipeline.

    Assumes usage like `first_action |then>> second_action`.

    Additional you can add any value to the beginning of the construction
    and >= after it to call the constructed chain with this value.

    You get something like this `value >= first_action |then>> second_action`.

    See `ActionChain` for more info.
    """
)(
    ActionChain()
)


to = documenting_by(
    """
    `PartialApplicationInfix` instance that implements `partial` as a pseudo
    operator.

    See `PartialApplicationInfix` for usage information.
    
    When called, creates a function that returns an input value, ignoring input
    arguments.
    """
)(
    _CallableCustomPartialApplicationInfix(
        partial,
        action_to_call=atomically(will(returned) |then>> eventually),
    )
)

by = documenting_by(
    """
    `PartialApplicationInfix` instance that implements `rpartial` as a pseudo
    operator.

    See `PartialApplicationInfix` for usage information.
    """
)(
    _CustomPartialApplicationInfix(rpartial)
)