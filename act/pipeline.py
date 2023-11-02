from functools import wraps, cached_property
from operator import not_
from typing import (
    Callable, Generic, Iterable, Iterator, Self, Any, Tuple, TypeAlias,
    Concatenate
)

from pyannotating import Special

from act.annotations import ActionT, R, Pm, V, A, B, C, D
from act.atomization import fun
from act.partiality import rpartial, will
from act.representations import code_like_repr_of
from act.synonyms import on
from act.tools import documenting_by, _get


__all__ = (
    "bind",
    "ActionChain",
    "then",
    "frm",
    "bind_by",
    "fbind_by",
    "discretely",
)


@documenting_by(
    """
    Function to call two input actions sequentially as one action in a
    pipeline form.

    Used as an atomic binding expression as a function in higher order
    functions (e.g. `reduce`), otherwise less preferred than the `then`
    pseudo-operator.
    """
)
@fun
class bind:
    def __init__(self, first: Callable[Pm, V], second: Callable[V, R]):
        self._first = first
        self._second = second

    def __repr__(self) -> str:
        return "({} >> {})".format(
            code_like_repr_of(self._first),
            code_like_repr_of(self._second),
        )

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._second(self._first(*args, **kwargs))


class ActionChain(Generic[ActionT]):
    """
    Class to create a pipeline from a collection of actions.

    Directly used to create from collections, in other cases it is less
    preferable than the `then` pseudo-operator.

    Iterable by its actions.

    Can get chain length by `len` function and subchain by `[]` referring to
    indexes of actions of a desired subchain.

    Each next action gets the output of the previous one.
    Value returned when called is value exited from the last action.

    If there are no actions, returns a input value back.
    """

    def __init__(self, actions: Iterable[ActionT | Self] = tuple()):
        self.__raw_actions = actions

    @cached_property
    def _actions(self) -> Tuple[ActionT]:
        new_actions = list()

        for action in self.__raw_actions:
            if isinstance(action, ActionChain):
                new_actions.extend(action)
            else:
                new_actions.append(action)

        del self.__raw_actions

        return tuple(new_actions)

    @cached_property
    def _main_action(self) -> ActionT:
        if len(self._actions) == 0:
            return _get

        def main_action(*args, **kwargs):
            result = self._actions[0](*args, **kwargs)

            for action in self._actions[1:]:
                result = action(result)

            return result

        return main_action

    def __repr__(self) -> str:
        return (
            " |then>> ".join(code_like_repr_of(action) for action in self._actions)
            if len(self._actions) > 1
            else f"ActionChain({str().join(map(code_like_repr_of, self._actions))})"
        )

    def __call__(self, *args, **kwargs) -> Any:
        return self._main_action(*args, **kwargs)

    def __iter__(self) -> Iterator[ActionT]:
        return iter(self._actions)

    def __len__(self) -> int:
        return len(self._actions)

    def __bool__(self) -> bool:
        return bool(self._actions)

    def __eq__(self, other: Special[Self]) -> bool:
        return isinstance(other, ActionChain) and self._actions == other._actions

    def __mul__(self, factor: int) -> Self:
        return type(self)(self._actions * factor)

    def __getitem__(self, key: int | slice) -> Self:
        actions = self._actions[key]

        return type(self)(actions if isinstance(actions, tuple) else (actions, ))


class _ActionChainInfix:
    _Operand: TypeAlias = Ellipsis | Callable | Iterable[Ellipsis | Callable]
    _NotCallable: TypeAlias = tuple | type(Ellipsis)

    def __init__(self, name: str, *, second: _Operand = _get):
        self._name = name
        self._second = second

    def __repr__(self) -> str:
        return f"|{self._name}>>"

    def __ror__(
        self,
        first: _Operand | Tuple[_Operand],
    ) -> ActionChain | Tuple[Ellipsis | Callable]:
        if (
            isinstance(first, self._NotCallable)
            or isinstance(self._second, self._NotCallable)
        ):
            return (*self.__as_tuple(first), *self.__as_tuple(self._second))

        return ActionChain([first, self._second])

    def __rshift__(self, second: _Operand) -> Self:
        return type(self)(
            self._name,
            second=second,
        )

    @staticmethod
    def __as_tuple(value: Tuple[V] | V) -> Tuple[V]:
        return value if isinstance(value, tuple) else (value, )


then = documenting_by(
    """
    `ActionChain` pseudo-operator to build an `ActionChain` and, accordingly,
    combine calls of several actions in a pipeline.

    Assumes usage like:
    ```
    first_action |then>> second_action
    ```

    See `ActionChain` for more info.
    """
)(
    _ActionChainInfix("then")
)


class _PipelineInfix:
    def __init__(self, name: str, *, argument_to_bind: A = None) -> None:
        self.__name = name
        self.__argument_to_bind = argument_to_bind

    def __str__(self) -> str:
        return f"|{self.__name}|"

    def __ror__(self, argument_to_bind: A) -> Self:
        return _PipelineInfix(self.__name, argument_to_bind=argument_to_bind)

    def __or__(
        self,
        action: Callable[Concatenate[A, Pm], R],
    ) -> Callable[Pm, R]:
        return action(self.__argument_to_bind)


frm = documenting_by(
    """
    Pseudo-operator for calling as in a pipeline.

    Assumes usage like:
    ```
    value |frm| action
    ```

    Left-associative, that is:
    ```
    value |frm| a |frm| b |frm| c == c(b(a(value)))
    ``
    """
)(
    _PipelineInfix('frm')
)


@documenting_by(
    """
    Function to create a function by insertion its input action in the input
    template.

    The created function replaces `...` with an input action.
    """
)
@fun
def bind_by(
    template: Iterable[Callable | Ellipsis],
) -> Callable[Callable, ActionChain]:
    @documenting_by(
        """
        Function given as a result of calling `bind_by`. See `bind_by` for more
        info.
        """
    )
    @fun
    def insert_to_template(intercalary_action: Callable) -> ActionChain:
        return ActionChain(
            intercalary_action if action is Ellipsis else action
            for action in template
        )

    return insert_to_template


fbind_by: Callable[
    Iterable[Callable | Ellipsis],
    Callable[Callable, Callable],
]
fbind_by = documenting_by(
    """`bind_by` linking actions to an indivisible `ActionChain`."""
)(fun(
    bind_by |then>> bind_by(... |then>> fun)
))


discretely: Callable[
    Callable[Callable[A, B], Callable[C, D]],
    Callable[ActionChain[Callable[A, B]] | Callable[A, B], Callable[C, D]],
]
discretely = documenting_by(
    """
    Function for decorator to map an action or actions of an `ActionChain` into
    an `ActionChain`.

    Maps an input decorator for each action individually.
    """
)(fun(
    will(map)
    |then>> bind_by(
        on(rpartial(isinstance, ActionChain) |then>> not_, lambda v: (v, ))
        |then>> ...
        |then>> ActionChain
    )
    |then>> fun
))


def _generating_pipeline(action: Callable[[ActionT, B], R]) -> Callable[
    [ActionT, B | _ActionChainInfix],
    R | ActionChain,
]:
    return wraps(action)(lambda first, second: (
        second.__ror__(first)
        if isinstance(second, _ActionChainInfix)
        else action(first, second)
    ))
