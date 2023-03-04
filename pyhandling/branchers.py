from functools import partial, reduce, wraps
from math import inf
from typing import Callable, Iterable, Any, Iterator, Self

from pyannotating import many_or_one, Special

from pyhandling.annotations import ResultT, handler, ArgumentsT, ResourceT, checker_of, PositiveConditionResultT, NegativeConditionResultT, FuncT, ErrorHandlingResultT, event_for
from pyhandling.binders import post_partial
from pyhandling.errors import HandlingRecursionDepthError
from pyhandling.tools import DelegatingProperty, collection_with_reduced_nesting_to, ArgumentPack, ArgumentKey
from pyhandling.synonyms import return_


class ActionChain(Generic[ResultT]):
    """
    Class combining calls of several functions together in sequential execution.

    Iterable by its nodes.

    Each next node gets the output of the previous one.
    Data returned when called is data exited from the last node.

    The first node is not bound to the standard handler interface and can be
    any callable object.

    Accordingly, delegates the call to that first handler, so it emulates its
    calling interface.

    If there are no nodes, returns the input resource back. If the arguments
    were not transmitted or there were too many, it throws
    NeutralActionChainError.

    Can be connected to another chain or handler using | between them with
    maintaining the position of the call.

    Also can be used >> to expand nodes starting from the end respectively.

    Has a one resource call synonyms >= and <= where is the chain on the right
    i.e. \"resource_to_call >= chain_instance\" and
    \"chain_instance <= resource_to_call\". 
    """

    def __init__(self, nodes: Iterable[Callable] = tuple()):
        self._nodes = tuple(nodes)

    def __call__(self, *args, **kwargs) -> ResultT:
        if not self._nodes:
            if len(args) != 1 or kwargs:
                raise NeutralActionChainError(
                    "ActionChain without nodes accepts only one argument and not{argumet_part}".format(
                        argumet_part=f"{' ' + str(len(args)) if len(args) != 1 else str()}{' with keyword' if kwargs else str()}"
                    )
                )

            return args[0]

        return reduce(
            lambda resource, node: node(resource),
            (self._nodes[0](*args, **kwargs), *self._nodes[1:])
        )

    def __iter__(self) -> Tuple[Callable]:
        return iter(self._nodes)

    def __rshift__(self, action_node: handler) -> Self:
        return self.__class__((*self.nodes, node))

    def __or__(self, action_node: handler) -> Self:
        return self.__class__((*self.nodes, node))

    def __ror__(self, node: handler) -> Self:
        return self.__class__((node, *self.nodes))

    def __le__(self, resource: Any) -> ResultT:
        return self(resource)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({' -> '.join(map(str, self._nodes))})"


def merge(*funcs: Callable, return_from: Special[None] = None) -> Special[tuple]:
    """
    Function to merge multiple functions with the same input interface into one.

    Functions are called in parallel, after which a tuple of their results is
    returned, in the order in which the functions were passed.

    It has an additional keyword only parameter return_from, which, if specified,
    will determine the result of the output function by getting a value from the
    resulting tuple by key.
    """

    def merged(*args, **kwargs) -> Special[tuple]:
        """
        Function that came out of the merge function is merged from other
        functions passed to the merge function.

        See merge for more info.
        """

        return (
            return_
            if return_from is None
            else post_partial(getitem_of, return_from)
        )(
            tuple(func(*args, **kwargs) for func in funcs)
        )

    return merged


def mergely(
    merge_function_factory: Callable[[*ArgumentsT], Callable[[...], ResultT]],
    *parallel_functions: Callable[[*ArgumentsT], Any],
    **keyword_parallel_functions: Callable[[*ArgumentsT], Any]
) -> Callable[[*ArgumentsT], ResultT]:
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


def recursively(
    resource_handler: Callable[[ResourceT], ResourceT],
    condition_checker: checker_of[ResourceT],
    *,
    max_recursion_depth: int = 1_000_000
) -> Callable[[ResourceT], ResourceT]:
    """
    Function to recursively handle input resource.

    If the result of handling for recursion is correct, it feeds the results
    of recursive_resource_handler to it, until the negative results of the
    recursion condition.

    Checks the condition of execution of the recursion by the correctness of the
    input resource or the result of the execution of the handler of the recursion
    resource.

    Limits the number of calls to max_recursion_depth by the argument. After the
    maximum expires, it causes the corresponding error.
    """

    def recursively_handle(resource: ResourceT) -> ResourceT:
        """
        Function emulating recursion that was created as a result of calling
        recursively.
        """

        for _ in range(max_recursion_depth):
            if condition_checker(resource):
                resource = resource_handler(resource)
            else:
                return resource

        raise HandlingRecursionDepthError(
            f"The number of recursive handling calls has exceeded the {max_recursion_depth} call limit."
        )

    return recursively_handle


def on_condition(
    condition_checker: Callable[[*ArgumentsT], bool],
    positive_condition_func: Callable[[*ArgumentsT], PositiveConditionResultT],
    *,
    else_: Callable[[*ArgumentsT], NegativeConditionResultT] = lambda *_, **__: None
) -> Callable[[*ArgumentsT], PositiveConditionResultT | NegativeConditionResultT]:
    """
    Function that implements the func choosing by condition.

    Creates a function that delegates the call to one other function selected by
    the results of condition_checker.

    If the condition is positive, selects positive_condition_func, if it is
    negative else_.
    """

    def brancher(*args, **kwargs) -> Any:
        """
        Function created by the on_condition function.
        See on_condition for more info.
        """

        return (
            positive_condition_func
            if condition_checker(*args, **kwargs)
            else else_
        )(*args, **kwargs)

    return brancher


def rollbackable(
    func: FuncT,
    rollbacker: Callable[[Exception], ErrorHandlingResultT]
) -> FuncT | ErrorHandlingResultT:
    """
    Decorator function providing handling of possible errors.
    Delegates error handling to rollbacker.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as error:
            return rollbacker(error)

    return wrapper


def returnly(
    func: Callable[[Any, ...], Any],
    *,
    argument_key_to_return: ArgumentKey = ArgumentKey(0)
) -> Callable[[Any, ...], Any]:
    """
    Decorator function that causes the input function to return not the result
    of its execution, but some argument that is incoming to it.

    Returns the first argument by default.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        func(*args, **kwargs)

        return ArgumentPack(args, kwargs)[argument_key_to_return]

    return wrapper


def eventually(func: event_for[ResultT]) -> ResultT:
    """
    Decorator function for constructing a function to which no input attributes
    will be passed.
    """

    return wraps(func)(lambda *args, **kwargs: func())


chain_constructor = Callable[[many_or_one[Callable]], ActionChain]