from functools import partial, reduce, wraps, cached_property, update_wrapper
from inspect import Signature, signature
from math import inf
from operator import itemgetter
from typing import Union, TypeAlias, TypeVar, Callable, Generic, Iterable, Iterator, Self, Any, Optional, Type

from pyannotating import many_or_one, Special, AnnotationTemplate, input_annotation

from pyhandling.annotations import ActionT, ResultT, one_value_action, P, action_for, reformer_of, ValueT, PositiveConditionResultT, NegativeConditionResultT, ErrorHandlingResultT, checker_of
from pyhandling.binders import right_partial
from pyhandling.errors import TemplatedActionChainError, NeutralActionChainError
from pyhandling.tools import calling_signature_of, contextual, DelegatingProperty, with_opened_items, ArgumentKey, ArgumentPack
from pyhandling.synonyms import returned


__all__ = (
    "ActionChain",
    "merged",
    "mergely",
    "repeating",
    "on",
    "rollbackable",
    "mapping_to_chain_of",
    "mapping_to_chain",
)


_NodeT = TypeVar("_NodeT", bound=Callable | Type[Ellipsis])


class bind:
    def __init__(
        self,
        first: Callable[P, ValueT],
        second: Callable[[ValueT], ResultT]
    ):
        self._first = first
        self._second = second

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self._second(self._first(*args, **kwargs))

    @cached_property
    def __signature__(self) -> Signature:
        return calling_signature_of(self._first).replace(
            return_annotation=calling_signature_of(self._second).return_annotation
        )


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

    def __init__(self, nodes: Iterable[_NodeT] = tuple()):
        self._is_template = Ellipsis in nodes
        self._nodes = tuple(nodes)

        if not self._is_template:
            self._main_action = (
                returned if len(self._nodes) == 0
                else reduce(bind, self._nodes)
            )

            update_wrapper(self, self._main_action)
            self.__signature__ = calling_signature_of(self._main_action)
        else:
            self._main_action = None

    def __call__(self, *args, **kwargs) -> Any:
        if self._is_template:
            raise TemplatedActionChainError("Templated ActionChain is not callable")

        return self._main_action(*args, **kwargs)

    def __iter__(self) -> Iterator[_NodeT]:
        return iter(self._nodes)

    def __len__(self) -> int:
        return len(self._nodes)

    def __bool__(self) -> bool:
        return len(self._nodes) != 0

    def __getitem__(self, key: int | slice) -> Self:
        return type(self)(as_collection(self._nodes[key]))

    def __repr__(self) -> str:
        return f"ActionChain({', '.join(map(str, self._nodes))})"

    def __str__(self) -> str:
        return (
            " |then>> ".join(
                '...' if node is Ellipsis else str(node) for node in self._nodes
            )
            if self._nodes
            else repr(self)
        )

    def __rshift__(self, node: Self | _NodeT) -> Self:
        return self.__with(node)

    def __or__(self, node: Self | _NodeT) -> Self:
        return self.__with(node)

    def __ror__(self, node: Self | _NodeT) -> Self:
        return self.__with(node, is_right=True)

    def __with(self, node: Self | _NodeT, *, is_right: bool = False) -> Self:
        other = node if isinstance(node, ActionChain) else ActionChain([node])

        return type(self)((*self, *other) if not is_right else (*other, *self))


def merged(
    *actions: Callable[P, Any],
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
            else itemgetter(return_from)
        )(
            tuple(action(*args, **kwargs) for action in actions)
        )

    return merged_actions


def mergely(
    merging_of: Callable[P, Callable[..., ResultT]],
    *parallel_actions: Callable[P, Any],
    **keyword_parallel_actions: Callable[P, Any]
) -> Callable[P, ResultT]:
    """
    Decorator that allows to initially separate several operations on
    input arguments and then combine these results in final operation.

    Gets the final merging action of the first input action by calling it
    with all the input arguments of the resulting (as a result of calling this
    particular action) action.

    Passes to the final merge action the results of calls to unbounded input
    actions (with the same arguments that were passed to the factory of this
    final merge action).

    When specifying parallel actions using keyword arguments, sets them to the
    final merging action through the same argument name through which they
    were specified.
    """

    @wraps(merging_of)
    def merger(*args: P.args, **kwargs: P.kwargs) -> ResultT:
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
    Function to call an input action multiple times.

    Initially calls an input action from an input value, after repeating the
    result of an input action itself.
    """

    @wraps(action)
    def repetitive_action(value: ValueT) -> ValueT:
        while is_valid_to_repeat(value):
            value = action(value)
        
        return value

    return repetitive_action


def on(
    condition_checker: Callable[P, bool],
    positive_condition_action: Callable[P, PositiveConditionResultT],
    *,
    else_: Callable[P, NegativeConditionResultT] = returned
) -> Callable[P, PositiveConditionResultT | NegativeConditionResultT]:
    """
    Function that implements action choosing by condition.

    Creates a action that delegates the call to one other action selected by
    the results of `condition_checker`.

    If the condition is positive, selects `positive_condition_action`, if it is
    negative, selects `else_`.

    With default `else_` takes one value actions.
    """

    def branch(*args: P.args, **kwargs: P.args) -> PositiveConditionResultT | NegativeConditionResultT:
        """
        Result function from `on` function.
        See `on` for more info.
        """

        return (
            positive_condition_action
            if condition_checker(*args, **kwargs)
            else else_
        )(*args, **kwargs)

    return branch


def rollbackable(
    action: Callable[P, ResultT],
    rollbacker: Callable[[Exception], ErrorHandlingResultT]
) -> Callable[P, ResultT | ErrorHandlingResultT]:
    """
    Decorator function providing handling of possible errors in an input action.
    """

    @wraps(action)
    def wrapper(*args: P.args, **kwargs: P.args) -> Any:
        try:
            return action(*args, **kwargs)
        except Exception as error:
            return rollbacker(error)

    return wrapper


mapping_to_chain_of = AnnotationTemplate(
    Callable,
    [[many_or_one[one_value_action]], AnnotationTemplate(ActionChain, [input_annotation])]
)

mapping_to_chain: TypeAlias = mapping_to_chain_of[one_value_action]