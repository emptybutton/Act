from abc import ABC, abstractmethod
from functools import cached_property, reduce
from inspect import Signature, Parameter, signature
from operator import not_, is_not, or_
from typing import (
    Callable, Any, _CallableGenericAlias, Optional, Tuple, Self, Iterable,
    NamedTuple, Generic
)

from pyannotating import Special

from act.annotations import Pm, V, R, I, A, dirty, ArgumentsT, ActionT, Unia
from act.atomization import func
from act.errors import ReturningError, MatchingError
from act.partiality import will, rpartial, partial, partially
from act.pipeline import bind, then
from act.representations import code_like_repr_of
from act.signatures import Decorator, call_signature_of
from act.synonyms import on
from act.tools import documenting_by, LeftCallable, items_of, _get


__all__ = (
    "returnly",
    "eventually",
    "with_result",
    "dynamically",
    "fmt",
    "double",
    "once",
    "via_indexer",
    "and_via_indexer",
    "with_repr_by",
    "decorate_with_repr_by",
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
    "when",
)


@documenting_by(
    """
    Decorator that causes an input action to return first argument that is
    incoming to it.
    """
)
@func
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
@func
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
            lambda item: (
                f"{code_like_repr_of(item[0])}={code_like_repr_of(item[1])}"
            ),
            self._kwargs.items(),
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


def with_result(result: R, action: Callable[Pm, Any]) -> LeftCallable[Pm, R]:
    """Function to force an input result for an input action."""

    return bind(action, to(result))


def dynamically(
    action: Callable[Pm, R],
    *argument_placeholders: Callable[Pm, Any],
    **keyword_argument_placeholders: Callable[Pm, Any],
) -> LeftCallable[Pm, R]:
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


def fmt(
    template: str,
    *actions: Callable[Pm, Any],
    **keyword_actions: Callable[Pm, Any],
) -> LeftCallable[Pm, str]:
    """Shortcut function for dynamic template formatting."""

    return dynamically(template.format, *actions, **keyword_actions)


@documenting_by(
    """
    Decorator to double call an input action.

    The first call is the call of an input action itself with the first
    positional argument, and the second is the call of its resulting action
    with the remaining arguments.
    """
)
@func
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
@func
class once(LeftCallable):
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
@func
class via_indexer:
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


@partially
class and_via_indexer(LeftCallable):
    """Decorator to add action call action via indexer."""

    def __init__(
        self,
        indexer: Callable[[..., I], A],
        main_action: Callable[Pm, R],
    ):
        self._indexer = indexer
        self._main_action = main_action

        self.__signature__ = call_signature_of(main_action)

    def __repr__(self) -> str:
        return (
            f"({code_like_repr_of(self._main_action)})"
            f"[{code_like_repr_of(self._indexer)}]"
        )

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._main_action(*args, **kwargs)

    def __getitem__(self, items: I | Tuple[I]) -> A:
        return self._indexer(*items_of(items))


@partially
class with_repr_by(LeftCallable):
    """Decorator to set `__repr__`."""

    def __init__(self, repr_of: Callable[ActionT, str], action: Unia[ActionT, Callable[Pm, R]]):
        self._action = action
        self._repr_of = repr_of

        self.__signature__ = call_signature_of(action)

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._action(*args, **kwargs)

    def __repr__(self) -> str:
        return self._repr_of(self._action)


@partially
def decorate_with_repr_by(
    decorated: Callable[ActionT, Callable[Pm, R]],
    action: ActionT,
) -> Callable[Pm, R]:
    return with_repr_by(
        to(f"{code_like_repr_of(decorated)}({code_like_repr_of(action)})"),
        decorated(action),
    )


class PartialApplicationInfix(ABC):
    """
    Infix class for action partial application.

    Used in the form `action |instance| argument` or `action |instance* arguments`
    if you want to unpack the arguments.
    """

    @abstractmethod
    def __or__(self, argument: Any) -> LeftCallable:
        ...

    @abstractmethod
    def __ror__(self, action_to_transform: Callable) -> Self | LeftCallable:
        ...

    @abstractmethod
    def __mul__(self, arguments: Iterable) -> LeftCallable:
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


class _CallableCustomPartialApplicationInfix(
    LeftCallable,
    _CustomPartialApplicationInfix,
):
    """
    `_CustomPartialApplicationInfix` delegating its call to the input action.
    """

    def __init__(
        self,
        transform: Callable[[Callable, V], Callable],
        *,
        action_to_call: Callable[Pm, R] = _get,
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
        action_to_call=func(will(_get) |then>> eventually),
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


shown: dirty[LeftCallable[V, V]]
shown = documenting_by("""Shortcut function for `returnly(print)`.""")(
    returnly(print)
)


yes: LeftCallable[bool, bool] = documenting_by("""Shortcut for `to(True)`.""")(
    to(True)
)


no: LeftCallable[bool, bool] = documenting_by("""Shortcut for `to(False)`.""")(
    to(False)
)


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
    is _get, in the order in which the actions were passed.
    """
)
@func
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
@func
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


def _is_else_branch(branch: Branch) -> bool:
    return branch.determinant is Ellipsis


def _else_action_from(branches: Iterable[Branch[Pm, R]]) -> Callable[Pm, R] | R:
    branches = tuple(branches)

    else_branches = tuple(
        branch for branch in branches if _is_else_branch(branch)
    )

    if len(else_branches) > 1:
        raise MatchingError("extra \"else\" branches")

    if else_branches:
        if branches.index(else_branches[0]) != len(branches) - 1:
            raise MatchingError("`else_` branch must be last")

        return else_branches[0].way

    return _get


# Unique object to annotate matching to an `else` branch in `when` or
# similar actions.
break_ = object()


def when(
    *branches: tuple[Special[Callable[Pm, bool]], Special[Callable[Pm, R] | R]],
) -> LeftCallable[Pm, R]:
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
    else_ = _else_action_from(branches)

    if else_ is break_:
        raise MatchingError("\"else\" branch recursion")

    branches = tuple(branch for branch in branches if not _is_else_branch(branch))

    if len(branches) == 0:
        return else_

    return on(
        branches[0].determinant,
        else_ if branches[0].way is break_ else branches[0].way,
        else_=(
            else_
            if len(branches) == 1
            else when(*branches[1:], Branch(Ellipsis, else_))
        ),
    )
