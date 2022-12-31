from enum import Enum, auto
from functools import reduce, wraps, partial
from typing import Callable, Iterable, Self, Optional

from pyhandling.tools import DelegatingProperty, Arguments


Handler = Callable[[any], any]


class HandlerKeeper:
    """
    Mixin class for conveniently getting handlers from an input collection and
    unlimited input arguments.
    """

    handlers = DelegatingProperty('_handlers')

    def __init__(self, handler_resource: Handler | Iterable[Handler], *handlers: Handler):
        self._handlers = (
            tuple(handler_resource)
            if isinstance(handler_resource, Iterable)
            else (handler_resource, )
        ) + handlers


class ReturnFlag(Enum):
    """
    Enum return method flags class.
    
    Describe the returned result from something (MultipleHandler).
    """

    first_received = auto()
    last_thing = auto()
    everything = auto()
    nothing = auto()


class MultipleHandler(HandlerKeeper):
    """
    Handler proxy class for representing multiple handlers as a single
    interface.

    Applies its handlers to a single resource.

    Return data is described using the ReturnFlag of the return_flag attribute.
    """

    def __init__(
        self,
        handler_resource: Handler | Iterable[Handler],
        *handlers: Handler,
        return_flag: ReturnFlag = ReturnFlag.first_received
    ):
        super().__init__(handler_resource, *handlers)
        self.return_flag = return_flag

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(map(str, self.handlers))})"

    def __call__(self, resource: any) -> any:
        result_of_all_handlers = list()

        for handler in self.handlers:
            handler_result = handler(resource)

            if self.return_flag == ReturnFlag.everything:
                result_of_all_handlers.append(handler_result)

            if self.return_flag == ReturnFlag.first_received and handler_result is not None:
                return handler_result

        if self.return_flag == ReturnFlag.everything:
            return result_of_all_handlers

        if self.return_flag == ReturnFlag.last_thing:
            return handler_result


class ActionChain(HandlerKeeper):  
    """
    Class that implements handling as a chain of actions of handlers.

    Each next handler gets the output of the previous one.
    Data returned when called is data exited from the last handler.

    If there are no handlers, spits out the input as output.

    Not strict on an input resource that, when called with no argument, is None.
    Used for chaining events.

    With the right treatment | to an instance creates another instance with the
    left handler ahead of the current chain handlers.

    Equivalently, it can be called >> in front, to equivalently create an chain,
    but the handlers of the current chain will be on the left.

    When referring to | or >> with another chain creates a chain with handlers in
    the same places, but integrates not the chain itself, but its handlers.
    """

    def __call__(self, *args, **kwargs) -> any:
        return reduce(
            lambda resource, handler: handler(resource),
            (self.handlers[0](*args, **kwargs), *self.handlers[1:])
        ) if self.handlers else resource

    def __rshift__(self, action_node: Handler) -> Self:
        return self.clone_with(action_node)

    def __or__(self, action_node: Handler) -> Self:
        return self.clone_with(action_node)

    def __ror__(self, action_node: Handler) -> Self:
        return self.clone_with(action_node, is_other_handlers_on_the_left=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({' -> '.join(map(str, self.handlers))})"

    def clone_with(self, *handlers: Handler, is_other_handlers_on_the_left: bool = False) -> Self:
        other_handlers = post_partial(get_collection_with_reduced_nesting, 1)(
            handler.handlers if isinstance(handler, ActionChain) else (handler, )
            for handler in handlers
        )

        handler_groph = [self.handlers, handlers]

        if is_other_handlers_on_the_left:
            handler_groph.reverse()

        return self.__class__(
            *handler_groph[0],
            *handler_groph[1],
        )


def on_condition(
    condition_resource_checker: Callable[[any], bool],
    positive_condition_handler: Handler,
    negative_condition_handler: Handler = lambda _: None
) -> Handler:
    """
    Function that implements branching handling of something according to a certain
    condition.

    Selects the appropriate handler based on the results of the
    condition_resource_checker.

    In case of a negative case and the absence of a negative case handler, returns
    None.
    """

    def branching_function(resource: any) -> any:
        return (
            positive_condition_handler
            if condition_resource_checker(resource)
            else negative_condition_handler
        )(resource)

    return branching_function


def separately(func: Callable[[], any]) -> any:
    """
    Decorator function for constructing a function to which no input attributes
    will be passed.
    """

    return wraps(func)(lambda *args, **kwargs: func())


class ContextManager:
    """
    Class that emulates the "with as" context manager.

    Creates a context using the context_factory attribute and returns the results
    of handling this context by the input context handler when called.
    """

    def __init__(self, context_factory: Callable[[], any]):
        self.context_factory = context_factory

    def __repr__(self) -> str:
        return f"<ContextManager for {self.context_factory}>"

    def __call__(self, context_handler: Handler) -> any:
        with self.context_factory() as context:
            return context_handler(context)


class ErrorHandlingController:
    """
    Controller class that delegates the handling of errors by error_handler that
    occur when delegating resource handling to resource_handler.
    """

    def __init__(self, resource_handler: Handler, error_handler: Callable[[Exception], any]):
        self.resource_handler = resource_handler
        self.error_handler = error_handler

    def __call__(self, resource: any):
        try:
            return self.resource_handler(resource)
        except Exception as error:
            return self.error_handler(error)


class ErrorRaiser:
    """Adapter class for raising an error using calling."""

    def __init__(self, error: Exception):
        self.error = error

    def __repr__(self) -> str:
        return f"<Riser of \"{self.error}\">"

    def __call__(self) -> None:
        raise self.error


class Mapper:
    """
    Map adapter class.

    Works just like map with the exception of returning already saved results.
    Can be replaced by ActionChain(partial(map, handler), tuple).
    """

    def __init__(self, handler: Handler):
        self.handler = handler

    def __repr__(self) -> str:
        return f"<Mapper of {self.handler}>"

    def __call__(self, collection: Iterable) -> tuple:
        return tuple(self.handler(item) for item in collection)


class Recurser:
    """
    Class to create recursion.

    If the result of handling for recursion is correct, it feeds the results
    of recursive_resource_handler to it, until the negative results of the
    recursion condition.

    Checks the condition of execution of the recursion by the correctness of the
    input resource or the result of the execution of the handler of the recursion
    resource.

    Delegates the determination of resource validity to the
    recursion_continuation_checker attribute.
    """

    def __init__(
        self,
        recursive_resource_handler: Handler,
        recursion_continuation_checker: Callable[[any], bool]
    ):
        self.recursive_resource_handler = recursive_resource_handler
        self.recursion_continuation_checker = recursion_continuation_checker

    def __call__(self, resource: any) -> any:
        while self.recursion_continuation_checker(resource):
            resource = self.recursive_resource_handler(resource)

        return resource


class CollectionExpander:
    """Class for getting a collection with additional elements."""
    
    def __init__(self, adding_items: Iterable):
        self.adding_items = adding_items

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} of [{', '.join(map(str, self.adding_items))}]>"

    def __call__(self, collection: Iterable) -> tuple:
        return (*collection, *self.adding_items)


def post_partial(func: Callable, *args, **kwargs) -> Callable:
    """
    Function equivalent to functools.partial but with the difference that
    additional arguments are added not before the incoming ones from the final
    call, but after.
    """

    @wraps(func)
    def wrapper(*wrapper_args, **wrapper_kwargs) -> any:
        return func(*wrapper_args, *args, **wrapper_kwargs, **kwargs)

    return wrapper


def mirror_partial(func: Callable, *args, **kwargs) -> Callable:
    """
    Function equivalent to pyhandling.handlers.rigth_partial but with the
    difference that additional arguments from this function call are unfolded.
    """

    return rigth_partial(func, *args[::-1], **kwargs)


def return_(resource: any) -> any:
    """
    Wrapper function for handling emulation through the functional use of the
    return statement.
    """

    return resource


def raise_(error: Exception) -> None:
    """Wrapper function for functional use of raise statement."""

    raise error


def call(caller: Callable, *args, **kwargs) -> any:
    """Function to call an input object and return the results of that call."""

    return caller(*args, **kwargs)


def additionally(action: Handler) -> Handler:
    """
    Function that allows to handle a resource but not return the results of its
    handling to continue the chain of handling this resource.
    """

    @wraps(action)
    def wrapper(resource: any) -> any:
        action(resource)
        return resource

    return wrapper


def take(resource: any) -> Callable[[], any]:
    """
    Function for creating an event that returns the input resource from this
    function.
    """

    return EventAdapter(lambda: resource)


then = ActionChain(tuple())
then.__doc__ = (
    """
    ActionChain class instance with no handlers.

    Used as an operator emulator for convenient construction of ActionChains.
    Assumes usage like \"first_handler |then>> second_handler\".

    See ActionChain for more info.
    """
)