from functools import partial, reduce, wraps, cached_property, update_wrapper
from inspect import Signature, signature
from math import inf
from operator import itemgetter
from typing import Union, TypeAlias, TypeVar, Callable, Generic, Iterable, Iterator, Self, Any, Optional, Type, Tuple

from pyannotating import many_or_one, Special, AnnotationTemplate, input_annotation

from pyhandling.annotations import ActionT, ResultT, one_value_action, P, action_for, reformer_of, ValueT, PositiveConditionResultT, NegativeConditionResultT, ErrorHandlingResultT, checker_of
from pyhandling.binders import right_partial
from pyhandling.errors import TemplatedActionChainError, NeutralActionChainError
from pyhandling.tools import calling_signature_of, contextual, DelegatingProperty, with_opened_items, ArgumentKey, ArgumentPack, annotation_sum
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
        self._nodes = tuple(nodes)
        self._is_template = Ellipsis in self._nodes

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

    def __le__(self, value: Any) -> Any:
        return self(value)

    def __iter__(self) -> Iterator[_NodeT]:
        return iter(self._nodes)

    def __len__(self) -> int:
        return len(self._nodes)

    def __bool__(self) -> bool:
        return len(self._nodes) != 0

    def __getitem__(self, key: int | slice) -> Self:
        return type(self)(as_collection(self._nodes[key]))

    def __repr__(self) -> str:
        return (
            " |then>> ".join(
                '...' if node is Ellipsis else str(node) for node in self._nodes
            )
            if self._nodes
            else "ActionChain()"
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


class merged:
    """
    Function to merge multiple functions with the same input interface into one.

    Functions are called in parallel, after which a tuple of their results is
    returned, in the order in which the functions were passed.
    """

    def __init__(self, *actions: Callable[P, Any]):
        self._actions = actions
        self.__signature__ = self.__get_signature()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Tuple:
        return tuple(action(*args, **kwargs) for action in actions)

    def __repr__(self) -> str:
        return ' & '.join(map(str, self._actions))

    def __get_signature(self) -> Signature:
        argument_signature = calling_signature_of(
            self._actions[0] if self._actions else lambda *_, **__: ...
        )

        return_annotation = partial(reduce, or_)(
            partial(filter, post_partial(is_not, _empty))(
                map(lambda act: calling_signature_of(act).return_annotation, self._actions)
            )
        )

        return argument_signature.replace(return_annotation=return_annotation)


class mergely:
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

    def __init__(
        self,
        merging_of: Callable[P, Callable[..., ResultT]],
        *parallel_actions: Callable[P, Any],
        **keyword_parallel_actions: Callable[P, Any],
    ):
        self._merging_of = merging_of
        self._parallel_actions = parallel_actions
        self._keyword_parallel_actions = keyword_parallel_actions

        self.__signature__ = self.__get_signature()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self._merging_of(*args, **kwargs)(
            *(
                parallel_action(*args, **kwargs)
                for parallel_action in self._parallel_actions
            ),
            **{
                _: keyword_parallel_action(*args, **kwargs)
                for _, keyword_parallel_action in self._keyword_parallel_actions.items()
            }
        )

    def __repr__(self) -> str:
        keyword_part = '='.join(
            f"{keyword}={action}"
            for keyword, action in self._keyword_parallel_actions.items()
        )

        return (
            f"mergely("
            f"{self._merging_of} -> ({', '.join(map(str, self._parallel_actions))}"
            f"{', ' if self._parallel_actions and self._keyword_parallel_actions else str()}"
            f"{keyword_part}"
            f'))'
        )

    def __get_signature(self) -> Signature:
        return_annotation = calling_signature_of(self._merging_of).return_annotation

        return calling_signature_of(self._merging_of).replace(
            return_annotation=(
                return_annotation.__args__[-1]
                if isinstance(return_annotation, _CallableGenericAlias)
                else _empty
            )
        )


class repeating:
    """
    Function to call an input action multiple times.

    Initially calls an input action from an input value, after repeating the
    result of an input action itself.
    """

    def __init__(self, action: reformer_of[ValueT], is_valid_to_repeat: checker_of[ValueT]):
        self._action = action
        self._is_valid_to_repeat = is_valid_to_repeat

        self.__signature__ = self.__get_signature()

    def __call__(self, value: ValueT) -> ValueT:
        while self._is_valid_to_repeat(value):
            value = self._action(value)
        
        return value

    def __repr__(self) -> str:
        return f"{self._action} while {self._is_valid_to_repeat}"

    def __get_signature(self) -> Signature:
        return calling_signature_of(self._action)


class on:
    """
    Function that implements action choosing by condition.

    Creates a action that delegates the call to one other action selected by
    the results of `condition_checker`.

    If the condition is positive, selects `positive_condition_action`, if it is
    negative, selects `else_`.

    With default `else_` takes one value actions.
    """

    def __init__(
        self,
        condition_checker: Callable[P, bool],
        positive_condition_action: Callable[P, PositiveConditionResultT],
        *,
        else_: Callable[P, NegativeConditionResultT] = returned
    ):
        self._condition_checker = condition_checker
        self._positive_condition_action = positive_condition_action
        self._negative_condition_action = else_

        self.__signature__ = self.__get_signature()

    def __call__(self, *args: P.args, **kwargs: P.args) -> PositiveConditionResultT | NegativeConditionResultT:
        return (
            self._positive_condition_action
            if self._condition_checker(*args, **kwargs)
            else self._negative_condition_action
        )(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            f"{self._positive_condition_action} on {self._condition_checker} "
            f"else {self._negative_condition_action}"
        )

    def __get_signature(self) -> Signature:
        return calling_signature_of(self._positive_condition_action).replace(
            return_annotation=annotation_sum(
                calling_signature_of(self._positive_condition_action).return_annotation,
                calling_signature_of(self._negative_condition_action).return_annotation,
            )
        )


class rollbackable:
    """
    Decorator function providing handling of possible errors in an input action.
    """

    def __init__(
        self,
        action: Callable[P, ResultT],
        rollback: Callable[[Exception], ErrorHandlingResultT],
    ):
        self._action = action
        self._rollback = rollback
        self.__signature__ = self.__get_signature()

    def __call__(*args: P.args, **kwargs: P.args) -> ResultT | ErrorHandlingResultT:
        try:
            return self._action(*args, **kwargs)
        except Exception as error:
            return self._rollback(error)

    def __repr__(self) -> str:
        return f"{self._action} ~> {self._rollback}"

    def __get_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(
            return_annotation=annotation_sum(
                calling_signature_of(self._action).return_annotation,
                calling_signature_of(self._rollback).return_annotation,
            )
        )


mapping_to_chain_of = AnnotationTemplate(
    Callable,
    [[many_or_one[one_value_action]], AnnotationTemplate(ActionChain, [input_annotation])]
)

mapping_to_chain: TypeAlias = mapping_to_chain_of[one_value_action]