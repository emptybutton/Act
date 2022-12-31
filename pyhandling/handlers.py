from enum import Enum, auto
from functools import reduce, wraps, partial
from math import inf
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


def handle_context(context_factory: Callable[[], any], context_handler: Handler):
    """
    Function for emulating the "with as" context manager.

    Creates a context using the context_factory and returns the results of
    handling this context by context_handler.
    """

    with context_factory() as context:
        return context_handler(context)


def rollbackable(func: Callable, rollbacker: Callable[[Exception], any]) -> Callable:
    """
    Decorator function providing handling of possible errors.
    Delegates error handling to rollbacker.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> any:
        try:
            return func(*args, **kwargs)
        except Exception as error:
            return rollbacker(error)

    return wrapper


def get_collection_from(*collections: Iterable) -> tuple:
    """Function to get a collection with elements from input collections."""

    return get_collection_with_reduced_nesting(collections, 1)


def recursively(condition_checker: Callable[[any], bool], resource_handler: Handler) -> any:
    """
    Function to recursively handle input resource.

    If the result of handling for recursion is correct, it feeds the results
    of recursive_resource_handler to it, until the negative results of the
    recursion condition.

    Checks the condition of execution of the recursion by the correctness of the
    input resource or the result of the execution of the handler of the recursion
    resource.
    """

    def recursively_handle(resource: any) -> any:
        while condition_checker(resource):
            resource = resource_handler(resource)

            return resource

    return recursively_handle


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


def call_method(object_: object, method_name: str, *args, **kwargs) -> any:
    return getattr(object_, method_name)(*args, **kwargs)


def get_collection_with_reduced_nesting(collection: Iterable, number_of_reductions: int = inf) -> tuple:
    reduced_collection = list()

    for item in collection:
        if not isinstance(item, Iterable):
            reduced_collection.append(item)
            continue

        reduced_collection.extend(
            reduce_collection_nesting(item, number_of_reductions - 1)
            if number_of_reductions > 1
            else item
        )

    return tuple(reduced_collection)


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

    return partial(return_, resource)


def showly(handler: Handler) -> ActionChain:
    handlers = handler.handlers if isinstance(handler, ActionChain) else (handler, )

    return ActionChain(
        get_collection_with_reduced_nesting(
            additionally(print) |then>> handler for handler in handlers
        )
    ) |then>> additionally(print)


then = ActionChain(tuple())
then.__doc__ = (
    """
    ActionChain class instance with no handlers.

    Used as an operator emulator for convenient construction of ActionChains.
    Assumes usage like \"first_handler |then>> second_handler\".

    See ActionChain for more info.
    """
)