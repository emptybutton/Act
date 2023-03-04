from functools import partial
from typing import Generic, Callable, Optional, Iterable, Any, Self

from pyannotating import Special

from pyhandling.annotations import ResultT
from pyhandling.binders import post_partial
from pyhandling.branchers import ActionChain
from pyhandling.tools import DelegatingProperty, documenting_by


__all__ = ("then", "to", "by")


class BindingInfix(Generic[ResultT]):
    """
    Infix class for binding functions with arguments.

    Used in the form \"func |instance| argument\" or \"func |instance* arguments\"
    if you want to unpack the arguments.
    """

    binder = DelegatingProperty("_binder")
    func = DelegatingProperty("_func")
    arguments = DelegatingProperty("_arguments")

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
    Neutral instance of the ActionChain class.

    Used as an operator emulator for convenient construction of ActionChains.
    Assumes usage like \"first_handler |then>> second_handler\".

    Additional you can add any resource to the beginning of the construction
    and >= after it to call the constructed chain with this resource.

    You get something like this \"resource >= first_handler |then>> second_handler\".

    See ActionChain for more info.
    """
)(
    ActionChain()
)


to = documenting_by(
    """
    BindingInfix instance that implements partial as a pseudo operator.

    See BindingInfix for usage information.
    """
)(
    BindingInfix(partial)
)

by = documenting_by(
    """
    BindingInfix instance that implements post_partial as a pseudo operator.

    See BindingInfix for usage information.
    """
)(
    BindingInfix(post_partial)
)