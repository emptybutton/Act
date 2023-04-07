from functools import partial
from typing import Generic, Callable, Optional, Iterable, Any, Self

from pyannotating import Special

from pyhandling.annotations import ResultT
from pyhandling.immutability import property_of
from pyhandling.branching import ActionChain
from pyhandling.partials import right_partial
from pyhandling.tools import documenting_by


__all__ = ("then", "to", "by")


class BindingInfix(Generic[ResultT]):
    """
    Infix class for binding functions with arguments.

    Used in the form `func |instance| argument` or `func |instance* arguments`
    if you want to unpack the arguments.
    """

    binder = property_of("_binder")
    func = property_of("_func")
    arguments = property_of("_arguments")

    def __init__(
        self,
        binder: Callable[[Callable, ...], Callable],
        func: Optional[Callable] = None,
        arguments: Optional[Iterable] = None
    ):
        self._binder = binder
        self._func = func
        self._arguments = arguments

    def __repr__(self) -> str:
        return f"BindingInfix for {self.binder.__name__ if hasattr(self.binder, '__name__') else self.binder}"

    def __or__(self, argument: Any) -> Callable:
        return self._binder(self._func, argument)

    def __ror__(self, func: Callable) -> Self | ResultT:
        return (
            type(self)(self.binder, func)
            if self.arguments is None
            else self._binder(func, *self.arguments)
        )

    def __mul__(self, arguments: Iterable) -> Callable:
        return type(self)(self.binder, arguments=arguments)


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
    `BindingInfix` instance that implements `partial` as a pseudo operator.

    See `BindingInfix` for usage information.
    """
)(
    BindingInfix(partial)
)

by = documenting_by(
    """
    `BindingInfix` instance that implements `right_partial` as a pseudo operator.

    See `BindingInfix` for usage information.
    """
)(
    BindingInfix(right_partial)
)