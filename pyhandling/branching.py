from functools import partial, reduce, update_wrapper
from inspect import Signature, Parameter
from operator import or_, is_not, not_
from typing import (
    TypeVar, Callable, Generic, Iterable, Iterator, Self, Any, Type,
    Tuple, NamedTuple, _CallableGenericAlias
)

from pyannotating import Special

from pyhandling.annotations import ActionT, R, Pm, V, A, B, C, D
from pyhandling.atoming import atomically
from pyhandling.errors import TemplatedActionChainError, MatchingError
from pyhandling.immutability import property_to, to_clone
from pyhandling.objects import of
from pyhandling.partials import rpartial, will
from pyhandling.signature_assignmenting import call_signature_of
from pyhandling.synonyms import returned, on
from pyhandling.tools import documenting_by, LeftCallable, action_repr_of


__all__ = (
    "bind",
    "ActionChain",
    "then",
    "binding_by",
    "merged",
    "mergely",
    "break_",
    "matching",
    "discretely",
)


class bind:
    """
    Function to call two input actions sequentially as one function in a
    pipeline form.

    Used as an atomic binding expression as a function in higher order
    functions (e.g. `reduce`), otherwise less preferred than the `then`
    pseudo-operator.
    """

    def __init__(self, first: Callable[Pm, V], second: Callable[V, R]):
        self._first = first
        self._second = second

        self.__signature__ = call_signature_of(self._first).replace(
            return_annotation=(call_signature_of(self._second).return_annotation)
        )

    def __repr__(self) -> str:
        return f"({action_repr_of(self._first)} >> {action_repr_of(self._second)})"

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._second(self._first(*args, **kwargs))


class ActionChain(LeftCallable, Generic[ActionT]):
    """
    Class to create a pipeline from a collection of actions.

    Iterable by its actions.

    Can get chain length by `len` function and subchain by `[]` referring to 
    indexes of actions of a desired subchain.

    Each next action gets the output of the previous one.
    Value returned when called is value exited from the last action.

    If there are no actions, returns a input value back.

    Has a one value call synonyms `>=` and `<=` where is the chain on the
    right i.e. `value >= instance` and less preferred `instance <= value`.

    Directly used to create from collections, in other cases it is less
    preferable than the `then` pseudo-operator.
    """

    is_template = property_to("_is_template")

    def __init__(self, actions: Iterable[ActionT | Ellipsis | Self] = tuple()):
        self._actions = self._actions_from(actions)
        self._is_template = Ellipsis in self._actions

        if not self._is_template:
            if len(self._actions) == 0:
                self._main_action = returned
            elif len(self._actions) == 1:
                self._main_action = self._actions[0]
            else:
                self._main_action = reduce(bind, self._actions)

            self.__signature__ = call_signature_of(self._main_action)
        else:
            self._main_action = None

    def __repr__(self) -> str:
        return (
            " |then>> ".join(
                '...' if action is Ellipsis else action_repr_of(action)
                for action in self._actions
            )
            if len(self._actions) > 1
            else f"ActionChain({str().join(map(action_repr_of, self._actions))})"
        )

    def __call__(self, *args, **kwargs) -> Any:
        if self._is_template:
            raise TemplatedActionChainError(
                "Templated ActionChain is not callable"
            )

        return self._main_action(*args, **kwargs)

    def __iter__(self) -> Iterator[ActionT]:
        return iter(self._actions)

    def __len__(self) -> int:
        return len(self._actions)

    def __bool__(self) -> bool:
        return bool(self._actions)

    def __getitem__(self, key: int | slice) -> Self:
        actions = self._actions[key]

        return type(self)(actions if isinstance(actions, tuple) else (actions, ))

    @staticmethod
    def _actions_from(
        actions: Iterable[ActionT | Ellipsis | Self],
    ) -> Tuple[ActionT | Ellipsis]:
        new_actions = list()

        for action in actions:
            if isinstance(action, ActionChain):
                new_actions.extend(action)
            else:
                new_actions.append(action)

        return tuple(new_actions)


class _ActionChainInfix:
    _second: Ellipsis | Callable = returned

    def __init__(self, name: str, *, second: Ellipsis | Callable = returned):
        self._name = name
        self._second = second

    def __repr__(self) -> str:
        return f"|{self._name}>>"

    def __ror__(self, first: Callable | Ellipsis) -> Self:
        return ActionChain([first, self._second])

    def __rshift__(self, second: Callable | Ellipsis) -> ActionChain:
        return type(self)(
            self._name,
            second=second,
        )


then = documenting_by(
    """
    `ActionChain` pseudo-operator to build an `ActionChain` and, accordingly,
    combine calls of several actions in a pipeline.

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

    See `ActionChain` for more info.
    """
)(
    _ActionChainInfix("then")
)


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

    def __init__(self, *actions: Callable[Pm, Any]):
        self._actions = actions
        self.__signature__ = self.__get_signature()

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> Tuple:
        return tuple(action(*args, **kwargs) for action in self._actions)

    def __repr__(self) -> str:
        return ' & '.join(map(action_repr_of, self._actions))

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
    Decorator to initially separate several operations on input arguments and
    then combine these results in final operation.

    Gets the final merging action of a first input action by calling it
    with all input arguments of the resulting (as a result of calling this
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
        merging_of: Callable[Pm, Callable[..., R]],
        *parallel_actions: Callable[Pm, Any],
        **keyword_parallel_actions: Callable[Pm, Any],
    ):
        self._merging_of = merging_of
        self._parallel_actions = parallel_actions
        self._keyword_parallel_actions = keyword_parallel_actions

        self.__signature__ = self.__get_signature()

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
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


class Branch(NamedTuple, Generic[Pm, R]):
    """NamedTuple to store an action to execute on a condition."""

    determinant: Special[Callable[Pm, bool]]
    way: Callable[Pm, R] | R


break_ = documenting_by(
    """
    Unique object to annotate matching to an `else` branch in `matching` or
    similar actions.
    """
)(
    of()
)


def matching(
    *branches: tuple[Special[Callable[Pm, bool]], Special[Callable[Pm, R] | R]],
) -> Callable[Pm, R]:
    """
    Function for using action matching like `if`, `elif` and `else` statements.

    Accepts branches as tuples, where in the first place is an action of
    checking the condition and in the second place is an action that implements
    the logic of this condition.

    When condition checkers are not callable, compares an input value with these
    check values.

    With non-callable implementations of the conditional logic, returns those
    non-callable values.

    When passing a branch with a checker as `...` (`Ellipsis`) initiates that
    branch as an "else" branch, which is performed only if the others are not
    performed.

    By default "else" branch returns an input value.

    There can only be one "else" branch.

    When passing a unique `break_` object as an implementation action, force a
    jump to the "else" branch.
    """

    branches = tuple(Branch(*branch) for branch in branches)

    else_branches = tuple(
        branch for branch in branches if branch.determinant is Ellipsis
    )

    if len(else_branches) > 1:
        raise MatchingError("Extra \"else\" branches")

    else_ = else_branches[0].way if else_branches else returned

    if else_ is break_:
        raise MatchingError("\"else\" branch recursion")

    branches = tuple(
        branch for branch in branches if branch.determinant is not Ellipsis
    )

    if len(branches) == 0:
        return else_

    return on(
        branches[0].determinant,
        else_ if branches[0].way is break_ else branches[0].way,
        else_=(
            else_
            if len(branches) == 1
            else matching(*branches[1:], Branch(Ellipsis, else_))
        ),
    )


discretely: Callable[
    Callable[[Callable[A, B]], Callable[C, D]],
    LeftCallable[ActionChain[Callable[A, B]] | Callable[A, B], Callable[C, D]],
]
discretely = documenting_by(
    """
    Function for decorator to map an action or actions of an `ActionChain` into
    an `ActionChain`.

    Maps an input decorator for each action individually.
    """
)(atomically(
    will(map)
    |then>> binding_by(
        on(rpartial(isinstance, ActionChain) |then>> not_, lambda v: (v, ))
        |then>> ...
        |then>> ActionChain
    )
    |then>> atomically
))
