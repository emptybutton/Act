from functools import partial, reduce, cached_property, update_wrapper
from inspect import Signature, Parameter
from operator import or_, is_not
from typing import (
    TypeAlias, TypeVar, Callable, Generic, Iterable, Iterator, Self, Any, Type,
    Tuple, NamedTuple, _CallableGenericAlias,
)

from pyannotating import (
    many_or_one, Special, AnnotationTemplate, input_annotation
)

from pyhandling.annotations import ResultT, one_value_action, P, ValueT
from pyhandling.atoming import atomically
from pyhandling.errors import TemplatedActionChainError
from pyhandling.immutability import property_to
from pyhandling.partials import rpartial
from pyhandling.signature_assignmenting import call_signature_of
from pyhandling.synonyms import returned, with_unpacking, on
from pyhandling.tools import documenting_by, with_attributes


__all__ = (
    "bind",
    "ActionChain",
    "binding_by",
    "merged",
    "mergely",
    "stop",
    "branching",
    "then",
    "mapping_to_chain_of",
    "mapping_to_chain",
)


_NodeT = TypeVar("_NodeT", bound=Callable | Type[Ellipsis])


@atomically
class bind:
    """
    Function to call two input actions sequentially as one function in the
    form of a pipeline.

    Used as an atomic binding expression as a function in higher order
    functions (e.g. `reduce`), otherwise less preferred than `then` operator.
    """

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
        return call_signature_of(self._first).replace(return_annotation=(
            call_signature_of(self._second).return_annotation
        ))


class ActionChain(Generic[_NodeT]):
    """
    Class combining calls of several functions together in sequential execution.

    Iterable by its nodes.

    Each next node gets the output of the previous one.
    Value returned when called is value exited from the last node.

    If there are no nodes, returns the input value back.

    Can be connected to another chain or action using `|` between them with
    maintaining the position of the call.

    Also can be used `>>` to expand nodes starting from the end respectively.

    Has a one value call synonyms `>=` and `<=` where is the chain on the
    right i.e. `input_value >= chain_instance` and less preferred
    `chain_instance <= input_value`.

    Directly used to create a pipeline from a collection of actions, in other
    cases it is less preferable than the `then` operator.
    """

    is_template = property_to("_is_template")

    def __init__(self, nodes: Iterable[_NodeT] = tuple()):
        self._nodes = tuple(nodes)
        self._is_template = Ellipsis in self._nodes

        if not self._is_template:
            self._main_action = (
                returned if len(self._nodes) == 0
                else reduce(bind, self._nodes)
            )

            update_wrapper(self, self._main_action)
            self.__signature__ = call_signature_of(self._main_action)
        else:
            self._main_action = None

    def __call__(self, *args, **kwargs) -> Any:
        if self._is_template:
            raise TemplatedActionChainError(
                "Templated ActionChain is not callable"
            )

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
        nodes = self._nodes[key]

        return type(self)(nodes if isinstance(nodes, tuple) else (nodes, ))

    def __repr__(self) -> str:
        return (
            " |then>> ".join(
                '...' if node is Ellipsis else str(node) for node in self._nodes
            )
            if len(self._nodes) > 1
            else f"ActionChain({', '.join(map(str, self._nodes))})"
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


def binding_by(
    template: Iterable[Callable | Ellipsis],
) -> Callable[[Callable], ActionChain]:
    """
    Function to create a function by insertion its input function in the input
    template.

    The created function replaces `...` with an input action.
    """

    def insert_to_template(intercalary_action: Callable) -> ActionChain:
        """
        Function given as a result of calling `binding_by`. See `binding_by`
        for more info.
        """

        return ActionChain(
            intercalary_action if action is Ellipsis else action
            for action in template
        )

    return insert_to_template


@atomically
class merged:
    """
    Function to merge multiple actions with the same input interface into one.

    Merged actions are called in parallel, after which a tuple of their results
    is returned, in the order in which the actions were passed.
    """

    def __init__(self, *actions: Callable[P, Any]):
        self._actions = actions
        self.__signature__ = self.__get_signature()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Tuple:
        return tuple(action(*args, **kwargs) for action in self._actions)

    def __repr__(self) -> str:
        return ' & '.join(map(str, self._actions))

    def __get_signature(self) -> Signature:
        if not self._actions:
            return call_signature_of(lambda *args, **kwargs: ...).replace(
                input_annotation=Tuple
            )

        argument_signature = call_signature_of(
            self._actions[0] if self._actions else lambda *_, **__: ...
        )

        return_annotations = tuple(
            partial(filter, rpartial(is_not, Parameter.empty))(map(
                lambda act: call_signature_of(act).return_annotation,
                self._actions
            ))
        )

        return_annotation = (
            reduce(or_, return_annotations)
            if return_annotations
            else Parameter.empty
        )

        return argument_signature.replace(return_annotation=return_annotation)


@atomically
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
                for _, keyword_parallel_action in (
                    self._keyword_parallel_actions.items()
                )
            }
        )

    def __repr__(self) -> str:
        return (
            f"mergely("
            f"{self._merging_of} -> ("
            f"{', '.join(map(str, self._parallel_actions))}"
            "{part_between_positions_and_keywords}"
            "{keyword_part}"
            f'))'
        ).format(
            part_between_positions_and_keywords=(
                ', '
                if self._parallel_actions and self._keyword_parallel_actions
                else str()
            ),
            keyword_part='='.join(
                f"{keyword}={action}"
                for keyword, action in self._keyword_parallel_actions.items()
            )
        )

    def __get_signature(self) -> Signature:
        return_annotation = call_signature_of(self._merging_of).return_annotation

        return call_signature_of(self._merging_of).replace(
            return_annotation=(
                return_annotation.__args__[-1]
                if isinstance(return_annotation, _CallableGenericAlias)
                else Parameter.empty
            )
        )


class _Fork(NamedTuple, Generic[P, ResultT]):
    """NamedTuple to store an action to execute on a condition."""

    determinant: Special[Callable[P, bool]]
    way: Callable[P, ResultT] | ResultT


stop = documenting_by(
    """
    Unique object to annotate branching to an `else` branch in `branching` or
    similar actions.
    """
)(
    with_attributes()
)


def branching(
    *forks: tuple[
        Special[Callable[P, bool]],
        Special[Callable[P, ResultT] | ResultT],
    ],
    else_: Callable[P, ResultT] | ResultT = returned,
) -> Callable[P, ResultT]:
    """
    Function for using action branching like `if`, `elif` and `else` statements.

    Accepts branches as tuples, where in the first place is the action of
    checking the condition and in the second place is the action that implements
    the logic of this condition.

    When condition checkers are not called, compares an input value with these
    check values.

    With non-callable implementations of the conditional logic, returns those
    non-callable values.

    With default `else_` takes actions of one value and returns an input value
    if none of the conditions are met.
    """

    forks = tuple(map(with_unpacking(_Fork), forks))

    if len(forks) == 0:
        return else_

    return on(
        forks[0].determinant,
        else_ if forks[0].way is stop else forks[0].way,
        else_=else_ if len(forks) == 1 else branching(*forks[1:], else_=else_)
    )


then = documenting_by(
    """
    Neutral instance of `ActionChain`.

    Used as a pseudo-operator to build an `ActionChain` and, accordingly,
    combine calls of several functions in a pipeline.

    Assumes usage like:
    ```
    first_action |then>> second_action
    ```

    Additional you can add any value to the beginning of the construction
    and >= after it to call the constructed chain with this value.

    You get something like this:
    ```
    value >= first_action |then>> second_action
    ```

    Optionally, the sequential use of this pseudo-operator can be shortened by
    replacing all but the first pseudo-operator with the `>>` operator:
    ```
    first |then>> second >> third >> fourth
    ```

    See `ActionChain` for a description of this pseudo-operator result behavior.
    """
)(
    ActionChain()
)


mapping_to_chain_of = AnnotationTemplate(
    Callable,
    [[one_value_action | ActionChain[one_value_action]], AnnotationTemplate(
        ActionChain,
        [input_annotation],
    )],
)

mapping_to_chain: TypeAlias = mapping_to_chain_of[one_value_action]
