from abc import ABC, abstractmethod
from functools import cached_property, partial, reduce
from inspect import Signature, Parameter, signature
from operator import not_, is_not, or_
from typing import (
    Callable, Any, _CallableGenericAlias, Optional, Tuple, Self, Iterable,
    NamedTuple, Generic
)

from pyannotating import Special

from pyhandling.annotations import (
    Pm, V, R, action_for, dirty, ArgumentsT, reformer_of
)
from pyhandling.atomization import atomically
from pyhandling.errors import ReturningError, MatchingError
from pyhandling.partiality import will, rpartial, flipped
from pyhandling.pipeline import bind, then
from pyhandling.representations import code_like_repr_of
from pyhandling.signatures import Decorator, call_signature_of
from pyhandling.synonyms import returned, on
from pyhandling.tools import documenting_by, LeftCallable


__all__ = (
    "returnly",
    "eventually",
    "with_result",
    "to_left",
    "to_right",
    "dynamically",
    "double",
    "once",
    "via_items",
    "PartialApplicationInfix",
    "to",
    "by",
    "shown",
    "yes",
    "no",
    "anything",
    "merged",
    "mergely",
    "Branch",
    "break_",
    "matching",
)


@documenting_by(
    """
    Decorator that causes an input action to return first argument that is
    incoming to it.
    """
)
@atomically
class returnly(Decorator):
    def __call__(self, value: V, *args, **kwargs) -> V:
        self._action(value, *args, **kwargs)

        return value

    @cached_property
    def _force_signature(self) -> Signature:
        parameters = tuple(call_signature_of(self._action).parameters.values())

        if len(parameters) == 0:
            raise ReturningError("Function must contain at least one parameter")

        return call_signature_of(self._action).replace(return_annotation=(
            parameters[0].annotation
        ))


@documenting_by(
    """
    Decorator function to call with predefined arguments instead of input ones.
    """
)
@atomically
class eventually(Decorator):
    def __init__(
        self,
        action: Callable[Pm, R],
        *args: Pm.args,
        **kwargs: Pm.kwargs,
    ):
        super().__init__(action)
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *_, **__) -> R:
        return self._action(*self._args, **self._kwargs)

    def __repr__(self) -> str:
        formatted_kwargs = ', '.join(map(
            lambda item: action_repr_of(item[0]) + '=' + action_repr_of(item[1]),
            self._kwargs.items()
        ))

        return (
            f"{type(self).__name__}({self._action}"
            f"{', ' if self._args or self._kwargs else str()}"
            f"{', '.join(map(code_like_repr_of, self._args))}"
            f"{', ' if self._args and self._kwargs else str()}"
            f"{formatted_kwargs})"
        )

    @cached_property
    def _force_signature(self) -> Signature:
        return call_signature_of(self._action).replace(parameters=(
            Parameter('_', Parameter.VAR_POSITIONAL, annotation=Any),
            Parameter('__', Parameter.VAR_KEYWORD, annotation=Any),
        ))


def with_result(result: R, action: Callable[Pm, Any]) -> Callable[Pm, R]:
    """Function to force an input result for an input action."""

    return bind(action, to(result))


@documenting_by(
    """Decorator to ignore all arguments except the first."""
)
@atomically
class to_left(Decorator):
    def __call__(self, left_: V, *_, **__) -> R:
        return self._action(left_)

    @property
    def _force_signature(self) -> Signature:
        signature_ = call_signature_of(self._action)

        return signature_.replace(parameters=[
            tuple(signature_.parameters.values())[0],
            *call_signature_of(lambda *_, **__: ...).parameters.values(),
        ])


to_right: LeftCallable[Callable[V, R], Callable[[..., V], R]]
to_right = documenting_by(
    """Decorator to ignore all arguments except the last."""
)(
    atomically(to_left |then>> flipped)
)


def dynamically(
    action: Callable[Pm, R],
    *argument_placeholders: Callable[Pm, Any],
    **keyword_argument_placeholders: Callable[Pm, Any],
) -> action_for[R]:
    """
    Function to dynamically determine arguments for an input action.

    Evaluates arguments from old arguments to places equal to the places of
    actions by which they are evaluated (including keywords).

    When passing values as argument evaluators, final computed values of such
    evaluators will be these values.
    """

    replaced = on(bind(callable, not_), to)

    return mergely(
        to(action),
        *map(replaced, argument_placeholders),
        **{
            _: replaced(value)
            for _, value in keyword_argument_placeholders.items()
        },
    )


@documenting_by(
    """
    Decorator to double call an input action.

    The first call is the call of an input action itself with the first
    positional argument, and the second is the call of its resulting action
    with the remaining arguments.
    """
)
@atomically
class double(Decorator):
    def __call__(
        self,
        value: Any,
        *result_action_args,
        **result_action_kwargs,
    ) -> Any:
        return self._action(value)(*result_action_args, **result_action_kwargs)

    @property
    def _force_signature(self) -> Signature:
        signature_ = call_signature_of(self._action)

        return signature_.replace(return_annotation=(
            signature_.return_annotation.__args__[-1]
            if isinstance(signature_, _CallableGenericAlias)
            else Parameter.empty
        ))


@dirty
@documenting_by(
    """
    Decorator for lazy action call.

    Calls an input action once, then returns a value of that first call,
    ignoring input arguments.
    """
)
@atomically
class once:
    _result: Optional[R] = None
    _was_called: bool = False

    def __init__(self, action: Callable[Pm, R]):
        self._action = action
        self.__signature__ = call_signature_of(self._action)

    def __repr__(self) -> str:
        return f"once({{}}{code_like_repr_of(self._action)})".format(
            f"{code_like_repr_of(self._result)} from "
            if self._was_called
            else str()
        )

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        if self._was_called:
            return self._result

        self._was_called = True
        self._result = self._action(*args, **kwargs)

        self.__signature__ = signature(lambda *_, **__: ...).replace(
            return_annotation=call_signature_of(self._action).return_annotation
        )

        return self._result


@documenting_by(
    """
    Decorator for an action, allowing it to be called via `[]` call rather than
    `()`.
    """
)
@atomically
class via_items:
    def __init__(
        self,
        action: Callable[[V], R] | Callable[[*ArgumentsT], R],
    ):
        self._action = action

    def __repr__(self) -> str:
        return "({})[{}]".format(
            code_like_repr_of(self._action),
            str(call_signature_of(self._action))[1:-1],
        )

    def __getitem__(self, key: V | Tuple[*ArgumentsT]) -> R:
        arguments = key if isinstance(key, tuple) else (key, )

        return self._action(*arguments)


class PartialApplicationInfix(ABC):
    """
    Infix class for action partial application.

    Used in the form `action |instance| argument` or `action |instance* arguments`
    if you want to unpack the arguments.
    """

    @abstractmethod
    def __or__(self, argument: Any) -> Callable:
        ...

    @abstractmethod
    def __ror__(self, action_to_transform: Callable) -> Self | Callable:
        ...

    @abstractmethod
    def __mul__(self, arguments: Iterable) -> Callable:
        ...


class _CustomPartialApplicationInfix(PartialApplicationInfix):
    """Named implementation of `PartialApplicationInfix` from input values."""

    def __init__(
        self,
        transform: Callable[[Callable, *ArgumentsT], Callable],
        *,
        action_to_transform: Optional[Callable] = None,
        arguments: Optional[Iterable[*ArgumentsT]] = None,
        name: Optional[str] = None,
    ):
        self._transform = transform
        self._action_to_transform = action_to_transform
        self._arguments = arguments
        self._name = "<PartialApplicationInfix>" if name is None else name

    def __repr__(self) -> str:
        return self._name

    def __or__(self, argument: Any) -> Callable:
        return self._transform(self._action_to_transform, argument)

    def __ror__(self, action_to_transform: Callable) -> Self | Callable:
        return (
            type(self)(
                self._transform,
                action_to_transform=action_to_transform,
                name=self._name,
            )
            if self._arguments is None
            else self._transform(action_to_transform, *self._arguments)
        )

    def __mul__(self, arguments: Iterable) -> Callable:
        return type(self)(self._transform, arguments=arguments, name=self._name)


class _CallableCustomPartialApplicationInfix(_CustomPartialApplicationInfix):
    """
    `_CustomPartialApplicationInfix` delegating its call to the input action.
    """

    def __init__(
        self,
        transform: Callable[[Callable, V], Callable],
        *,
        action_to_call: Callable[Pm, R] = returned,
        action_to_transform: Optional[Callable] = None,
        arguments: Optional[Iterable[V]] = None,
        name: Optional[str] = None
    ):
        super().__init__(
            transform,
            action_to_transform=action_to_transform,
            arguments=arguments,
            name=name,
        )
        self._action_to_call = action_to_call

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._action_to_call(*args, **kwargs)


to = documenting_by(
    """
    `PartialApplicationInfix` instance that implements `partial` as a pseudo
    operator.

    See `PartialApplicationInfix` for usage information.

    When called, creates a function that returns an input value, ignoring input
    arguments.
    """
)(
    _CallableCustomPartialApplicationInfix(
        partial,
        name='to',
        action_to_call=atomically(will(returned) |then>> eventually),
    )
)


by = documenting_by(
    """
    `PartialApplicationInfix` instance that implements `rpartial` as a pseudo
    operator.

    See `PartialApplicationInfix` for usage information.
    """
)(
    _CustomPartialApplicationInfix(rpartial, name='by')
)


shown: dirty[reformer_of[V]]
shown = documenting_by("""Shortcut function for `returnly(print)`.""")(
    returnly(print)
)


yes: action_for[bool] = documenting_by("""Shortcut for `to(True)`.""")(to(True))
no: action_for[bool] = documenting_by("""Shortcut for `to(False)`.""")(to(False))


class _ForceComparable:
    """Class for objects that are aware of the results of their `==` checks."""

    def __init__(self, name: str, *, forced_sign: bool):
        self._name = name
        self._forced_sign = forced_sign

    def __repr__(self) -> str:
        return self._name

    def __eq__(self, _: Any) -> bool:
        return self._forced_sign


anything = documenting_by(
    """Special object always returning `True` when `==` is checked."""
)(
    _ForceComparable("anything", forced_sign=True)
)


@documenting_by(
    """
    Function to merge multiple actions with the same input interface into one.

    Merged actions are called in parallel, after which a tuple of their results
    is returned, in the order in which the actions were passed.
    """
)
@atomically
class merged:
    def __init__(self, *actions: Callable[Pm, Any]):
        self._actions = actions
        self.__signature__ = self.__get_signature()

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> Tuple:
        return tuple(action(*args, **kwargs) for action in self._actions)

    def __repr__(self) -> str:
        return ' & '.join(map(code_like_repr_of, self._actions))

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


@documenting_by(
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
)
@atomically
class mergely:
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


# Unique object to annotate matching to an `else` branch in `matching` or
# similar actions.
break_ = object()


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
