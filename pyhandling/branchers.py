from functools import partial, reduce, wraps
from math import inf
from typing import Generic, Iterable, Callable, Tuple, Self, Any

from pyannotating import many_or_one, Special

from pyhandling.annotations import ActionT, ResultT, atomic_action, ArgumentsT, reformer_of, ResourceT, checker_of, PositiveConditionResultT, NegativeConditionResultT, ErrorHandlingResultT, event_for
from pyhandling.binders import post_partial
from pyhandling.errors import NeutralActionChainError
from pyhandling.tools import open_collection_items, ArgumentKey, ArgumentPack
from pyhandling.synonyms import return_


__all__ = (
    "ActionChain", "merge", "mergely", "repeating", "on_condition",
    "rollbackable", "chain_constructor"
)


class ActionChain(Generic[ActionT]):
    """
    Class combining calls of several functions together in sequential execution.

    Iterable by its nodes.

    Each next node gets the output of the previous one.
    Data returned when called is data exited from the last node.

    If there are no nodes, returns the input resource back. If the arguments
    were not transmitted or there were too many, it throws
    `NeutralActionChainError`.

    Can be connected to another chain or action using `|` between them with
    maintaining the position of the call.

    Also can be used `>>` to expand nodes starting from the end respectively.

    Has a one resource call synonyms `>=` and `<=` where is the chain on the
    right i.e. `resource_to_call >= chain_instance` and less preferred
    `chain_instance <= resource_to_call`. 
    """

    def __init__(self, nodes: Iterable[many_or_one[ActionT]] = tuple()):
        self._nodes = open_collection_items(nodes)

    def __call__(self, *args, **kwargs) -> ResultT:
        if not self._nodes:
            if len(args) != 1 or kwargs:
                raise NeutralActionChainError(
                    "ActionChain without nodes accepts only one argument, not{argumet_part}".format(
                        argumet_part=f"{' ' + str(len(args)) if len(args) != 1 else str()}{' with keywords' if kwargs else str()}"
                    )
                )

            return args[0]

        return reduce(
            lambda resource, node: node(resource),
            (self._nodes[0](*args, **kwargs), *self._nodes[1:])
        )

    def __iter__(self) -> Tuple[ActionT]:
        return iter(self._nodes)

    def __rshift__(self, node: atomic_action) -> Self:
        return self.__class__((*self._nodes, node))

    def __or__(self, node: atomic_action) -> Self:
        return self.__class__((*self._nodes, node))

    def __ror__(self, node: atomic_action) -> Self:
        return self.__class__((node, *self._nodes))

    def __le__(self, resource: Any) -> ResultT:
        return self(resource)

    def __repr__(self) -> str:
        return " |then>> ".join(
            node.__name__ if hasattr(node, "__name__") else str(node)
            for node in self._nodes
        )


def merge(*actions: Callable, return_from: Special[None] = None) -> Special[tuple]:
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
            tuple(action(*args, **kwargs) for action in actions)
        )

    return merged


def mergely(
    parallel_action_result_merging_of: Callable[[*ArgumentsT], action_for[ResultT]],
    *parallel_actions: Callable[[*ArgumentsT], Any],
    **keyword_parallel_actions: Callable[[*ArgumentsT], Any]
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

    @wraps(parallel_action_result_merging_of)
    def merger(*args, **kwargs) -> ResultT:
        return parallel_action_result_merging_of(*args, **kwargs)(
            *(
                parallel_action(*args, **kwargs)
                for parallel_action in parallel_actions
            ),
            **{
                _: keyword_parallel_action(*args, **kwargs)
                for _, keyword_parallel_action in keyword_parallel_actions.items()
            }
        )

    return merger


def repeating(
    action: reformer_of[ResourceT],
    is_valid_to_repeat: Callable[[ResourceT], bool]
) -> Callable[[ResourceT], ResourceT]:
    """
    Function for repeatedly calling the input function of its own result.

    Specifies the application and repetition in particular, using the
    `is_valid_to_repeat` parameter.
    """

    @wraps(action)
    def repetitive_action(resource: ResourceT) -> ResourceT:
        while is_valid_to_repeat(resource):
            resource = action(resource)
        
        return resource

    return repetitive_action


def on_condition(
    condition_checker: Callable[[*ArgumentsT], bool],
    positive_condition_action: Callable[[*ArgumentsT], PositiveConditionResultT],
    *,
    else_: Callable[[*ArgumentsT], NegativeConditionResultT] = lambda *_, **__: None
) -> Callable[[*ArgumentsT], PositiveConditionResultT | NegativeConditionResultT]:
    """
    Function that implements the function choosing by condition.

    Creates a function that delegates the call to one other function selected by
    the results of `condition_checker`.

    If the condition is positive, selects `positive_condition_action`, if it is
    negative -> `else_`.
    """

    def brancher(*args, **kwargs) -> Any:
        """
        Function created by the `on_condition` function.
        See `on_condition` for more info.
        """

        return (
            positive_condition_action
            if condition_checker(*args, **kwargs)
            else else_
        )(*args, **kwargs)

    return brancher


def rollbackable(
    action: Callable[[*ArgumentsT], ResultT],
    rollbacker: Callable[[Exception], ErrorHandlingResultT]
) -> Callable[[*ArgumentsT], ResultT | ErrorHandlingResultT]:
    """
    Decorator function providing handling of possible errors.
    Delegates error handling to `rollbacker`.
    """

    @wraps(action)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return action(*args, **kwargs)
        except Exception as error:
            return rollbacker(error)

    return wrapper


chain_constructor = Callable[[Iterable[many_or_one[Callable]]], ActionChain]