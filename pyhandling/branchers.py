from enum import Enum, auto
from functools import reduce, wraps, partial
from typing import Iterable, Callable, Self, Optional

from pyhandling.annotations import Handler, Event, checker_of, factory_of, handler_of
from pyhandling.binders import post_partial
from pyhandling.tools import DelegatingProperty, ArgumentPack, ArgumentKey, get_collection_with_reduced_nesting
from pyhandling.synonyms import return_


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
            return tuple(result_of_all_handlers)

        if self.return_flag == ReturnFlag.last_thing:
            return handler_result


class ActionChain:
    """
    Class that implements handling as a chain of actions of handlers.

    In the presence of basic chains (strictly instances of the ActionChain class)
    in the rows of handlers, takes their handlers instead of them.

    Each next handler gets the output of the previous one.
    Data returned when called is data exited from the last handler.

    The first handler is not bound to the standard handler interface and can be
    any callable object.

    Accordingly, delegates the call to that first handler, so it emulates its
    interface.

    If there are no handlers, returns an argument pack from an input arguments.

    Can be connected to another chain or handler using | between them with
    maintaining the position of the call.

    Also can be used >> to expand handlers starting from the end respectively.
    """

    handlers = DelegatingProperty('_handlers')

    def __init__(
        self,
        opening_handler_resource: Callable | Iterable[Callable] = tuple(),
        *handlers: Handler
    ):
        self._handlers = self.get_with_aligned_chains(
            (
                tuple(opening_handler_resource)
                if isinstance(opening_handler_resource, Iterable)
                else (opening_handler_resource, )
            )
            + handlers
        )

    def __call__(self, *args, **kwargs) -> any:
        return reduce(
            lambda resource, handler: handler(resource),
            (self.handlers[0](*args, **kwargs), *self.handlers[1:])
        ) if self.handlers else ArgumentPack(args, kwargs)

    def __rshift__(self, action_node: Handler) -> Self:
        return self.clone_with(action_node)

    def __or__(self, action_node: Handler) -> Self:
        return self.clone_with(action_node)

    def __ror__(self, action_node: Handler) -> Self:
        return self.clone_with(action_node, is_other_handlers_on_the_left=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({' -> '.join(map(str, self.handlers))})"

    def clone_with(self, *handlers: Handler, is_other_handlers_on_the_left: bool = False) -> Self:
        """
        Method for cloning the current chain instance with additional handlers
        from unlimited arguments.

        Additional handlers can be added to the beginning of the chain if
        `is_other_handlers_on_the_left = True`.
        """

        handler_groph = [self.handlers, handlers]

        if is_other_handlers_on_the_left:
            handler_groph.reverse()

        return self.__class__(
            *handler_groph[0],
            *handler_groph[1],
        )

    def clone_with_intermediate(
        self,
        intermediate_handler: Handler,
        *,
        is_on_input: bool = False,
        is_on_output: bool = False
    ) -> Self:
        """
        Method for cloning the current chain with an additional handler between
        the current chain handlers.

        Also, the intermediate handler can add to the end and/or to the beginning
        of the chain with is_on_input and/or is_on_output = True.
        """

        if not self.handlers:
            return self

        return ActionChain(
            ((intermediate_handler, ) if is_on_input else tuple())
            + ((
                self.handlers[0] |then>> ActionChain(
                    post_partial(get_collection_with_reduced_nesting, 1)(
                        intermediate_handler |then>> handler
                        for handler in self.handlers[1:]
                    )
                )
            ), )
            + ((intermediate_handler, ) if is_on_output else tuple())
        )

    @staticmethod
    def get_with_aligned_chains(handlers: Iterable[Handler]) -> tuple[Handler]:
        """
        Function for getting homogeneous handlers without unnecessary chain
        instances.
        """

        return post_partial(get_collection_with_reduced_nesting, 1)(
            handler.handlers if type(handler) is ActionChain else (handler, )
            for handler in handlers
        )


def mergely(
    merge_function_factory: factory_of[Callable],
    *parallel_functions: factory_of[any],
    **keyword_parallel_functions: factory_of[any]
):
    """
    Decorator function that allows to initially separate several operations on
    input arguments and then combine these results in final operation.

    Gets the final merging function of the first input function by calling it
    with all the input arguments of the resulting (as a result of calling this
    particular function) function.

    Passes to the final merge function the results of calls to unbounded input
    functions (with the same arguments that were passed to the factory of this
    final merge function).

    When specifying parallel functions using keyword arguments, sets them to the
    final merging function through the same argument name through which they
    were specified.
    """

    @wraps(merge_function_factory)
    def wrapper(*args, **kwargs):
        return merge_function_factory(*args, **kwargs)(
            *(
                parallel_function(*args, **kwargs)
                for parallel_function in parallel_functions
            ),
            **{
                kwarg: keyword_parallel_function(*args, **kwargs)
                for kwarg, keyword_parallel_function in keyword_parallel_functions.items()
            }
        )

    return wrapper


def recursively(resource_handler: Handler, condition_checker: checker_of[any]) -> any:
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
        """
        Function emulating recursion that was created as a result of calling
        recursively.
        """

        while condition_checker(resource):
            resource = resource_handler(resource)

        return resource

    return recursively_handle


def on_condition(checker: Callable[..., bool], func: Callable, *, else_: Optional[Callable] = None) -> Callable:
    """
    Function that implements branching of something according to a
    certain condition.

    Selects the appropriate handler based on the results of the
    condition_resource_checker.

    In case of a negative case and the absence of a negative case handler (else_),
    returns None.
    """

    if else_ is None:
        else_ = eventually(partial(return_, None))

    @wraps(func)
    def wrapper(*args, **kwargs) -> any:
        return (func if checker(*args, **kwargs) else else_)(*args, **kwargs)

    return wrapper


def rollbackable(func: Callable, rollbacker: handler_of[Exception]) -> Callable:
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


def returnly(
    func: Callable[[any, ...], any],
    *,
    argument_key_to_return: ArgumentKey = ArgumentKey(0)
) -> Callable[[any, ...], any]:
    """
    Decorator function that causes the input function to return not the result
    of its execution, but some argument that is incoming to it.

    Returns the first argument by default.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> any:
        func(*args, **kwargs)

        return ArgumentPack(args, kwargs)[argument_key_to_return]

    return wrapper


def eventually(func: Event) -> any:
    """
    Decorator function for constructing a function to which no input attributes
    will be passed.
    """

    return wraps(func)(lambda *args, **kwargs: func())


then = ActionChain()
then.__doc__ = (
    """
    Neutral instance of the ActionChain class.

    Used as an operator emulator for convenient construction of ActionChains.
    Assumes usage like \"first_handler |then>> second_handler\".

    See ActionChain for more info.
    """
)