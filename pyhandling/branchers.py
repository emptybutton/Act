from functools import partial, reduce, wraps
from math import inf
from typing import TypeAlias, TypeVar, Callable, Generic, Iterable, Iterator, Self, Any, Optional

from pyannotating import many_or_one, Special, AnnotationTemplate, input_annotation

from pyhandling.annotations import ActionT, ResultT, atomic_action, ArgumentsT, action_for, reformer_of, ValueT, PositiveConditionResultT, NegativeConditionResultT, ErrorHandlingResultT, checker_of
from pyhandling.binders import post_partial
from pyhandling.errors import TemplatedActionChainError, NeutralActionChainError
from pyhandling.tools import DelegatingProperty, with_opened_items, ArgumentKey, ArgumentPack
from pyhandling.synonyms import returned, getitem


__all__ = (
    "ActionChain", "merged", "mergely", "repeating", "on", "rollbackable",
    "mapping_to_chain_of", "mapping_to_chain"
)


_NodeT: TypeAlias = TypeVar("_NodeT", bound=Callable | Ellipsis)


class ActionChain(Generic[_NodeT]):
    """
    Class combining calls of several functions together in sequential execution.

    Iterable by its nodes.

    Each next node gets the output of the previous one.
    Value returned when called is value exited from the last node.

    If there are no nodes, returns the input value back. If the arguments were
    not transmitted or there were too many, it throws `NeutralActionChainError`.

    Can be connected to another chain or action using `|` between them with
    maintaining the position of the call.

    Also can be used `>>` to expand nodes starting from the end respectively.

    Has a one value call synonyms `>=` and `<=` where is the chain on the
    right i.e. `input_value >= chain_instance` and less preferred
    `chain_instance <= input_value`. 
    """

    is_template = DelegatingProperty("_is_template")

    def __init__(self, nodes: Iterable[many_or_one[_NodeT]] = tuple()):
        self._nodes = with_opened_items(nodes)
        self._is_template = Ellipsis in self._nodes

    def __call__(self, *args, **kwargs) -> ResultT:
        if self._is_template:
            raise TemplatedActionChainError("Templated ActionChain is not callable")

        if not self._nodes:
            if len(args) != 1 or kwargs:
                raise NeutralActionChainError(
                    "ActionChain without nodes accepts only one argument, not{argumet_part}".format(
                        argumet_part=f"{' ' + str(len(args)) if len(args) != 1 else str()}{' with keywords' if kwargs else str()}"
                    )
                )

            return args[0]

        return reduce(
            lambda value, node: node(value),
            (self._nodes[0](*args, **kwargs), *self._nodes[1:])
        )

    def __iter__(self) -> Iterator[_NodeT]:
        return iter(self._nodes)

    def __rshift__(self, node: atomic_action) -> Self:
        return self.__class__((*self._nodes, node))

    def __or__(self, node: atomic_action) -> Self:
        return self.__class__((*self._nodes, node))

    def __ror__(self, node: atomic_action) -> Self:
        return self.__class__((node, *self._nodes))

    def __le__(self, value: Any) -> ResultT:
        return self(value)

    def __repr__(self) -> str:
        return (
            " |then>> ".join(map(self._fromat_node, self._nodes))
            if self._nodes else f"{self.__class__.__name__}()"
        )

    def _fromat_node(self, node: Special[Ellipsis, _NodeT]) -> str:
        if node is Ellipsis:
            return '...'

        return node.__name__ if hasattr(node, "__name__") else str(node)


def merged(
    *actions: Callable[[*ArgumentsT], Any],
    return_from: Optional[int | slice] = None,
) -> Special[tuple]:
    """
    Function to merge multiple functions with the same input interface into one.

    Functions are called in parallel, after which a tuple of their results is
    returned, in the order in which the functions were passed.

    It has an additional keyword only parameter `return_from`, which, if specified,
    will determine the result of the output function by getting a value from the
    resulting tuple by key.
    """

    def merged_actions(*args, **kwargs) -> Special[tuple]:
        """
        Function that came out of the `merged` function is merged from other
        functions passed to the merge function.

        See `merged` for more info.
        """

        return (
            returned
            if return_from is None
            else post_partial(getitem, return_from)
        )(
            tuple(action(*args, **kwargs) for action in actions)
        )

    return merged_actions


def mergely(
    merging_of: Callable[[*ArgumentsT], action_for[ResultT]],
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

    @wraps(merging_of)
    def merger(*args, **kwargs) -> ResultT:
        return merging_of(*args, **kwargs)(
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
    action: reformer_of[ValueT],
    is_valid_to_repeat: checker_of[ValueT],
) -> reformer_of[ValueT]:
    """
    Function for repeatedly calling the input function of its own result.

    Specifies the application and repetition in particular, using the
    `is_valid_to_repeat` parameter.
    """

    @wraps(action)
    def repetitive_action(value: ValueT) -> ValueT:
        while is_valid_to_repeat(value):
            value = action(value)
        
        return value

    return repetitive_action


def on(
    condition_checker: Callable[[*ArgumentsT], bool],
    positive_condition_action: Callable[[*ArgumentsT], PositiveConditionResultT],
    *,
    else_: Callable[[*ArgumentsT], NegativeConditionResultT] = returned
) -> Callable[[*ArgumentsT], PositiveConditionResultT | NegativeConditionResultT]:
    """
    Function that implements action choosing by condition.

    Creates a action that delegates the call to one other action selected by
    the results of `condition_checker`.

    If the condition is positive, selects `positive_condition_action`, if it is
    negative, then else_.

    With default `else_` takes actions of one argument.
    """

    def brancher(*args, **kwargs) -> Any:
        """
        Result function from `on` function.
        See `on` for more info.
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


mapping_to_chain_of = AnnotationTemplate(
    Callable,
    [[many_or_one[atomic_action]], AnnotationTemplate(ActionChain, [input_annotation])]
)

mapping_to_chain: TypeAlias = mapping_to_chain_of[atomic_action]