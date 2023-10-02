from functools import reduce, wraps
from operator import attrgetter, not_
from typing import Callable, Generic, Iterable, Iterator, Self, Any, Tuple

from pyannotating import Special

from act.annotations import ActionT, R, Pm, V, A, B, C, D
from act.errors import TemplatedActionChainError
from act.atomization import fun
from act.partiality import rpartial, will
from act.representations import code_like_repr_of
from act.signatures import call_signature_of
from act.synonyms import on
from act.tools import documenting_by, _get


__all__ = (
    "bind",
    "ActionChain",
    "then",
    "binding_by",
    "atomic_binding_by",
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

        self.__signature__ = call_signature_of(self._first).replace(
            return_annotation=(call_signature_of(self._second).return_annotation)
        )

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
        self._actions = self._actions_from(actions)

        if len(self._actions) == 0:
            self._main_action = _get
        elif len(self._actions) == 1:
            self._main_action = self._actions[0]
        else:
            self._main_action = reduce(bind, self._actions)

        self.__signature__ = call_signature_of(self._main_action)

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

    @staticmethod
    def _actions_from(
        actions: Iterable[ActionT | Self],
    ) -> Tuple[ActionT]:
        new_actions = list()

        for action in actions:
            if isinstance(action, ActionChain):
                new_actions.extend(action)
            else:
                new_actions.append(action)

        return tuple(new_actions)


class _ActionChainInfix:
    _Operand: TypeAlias = Ellipsis | Callable | Iterable[Ellipsis | Callable]
    _NotCallable: TypeAlias = tuple | type(Ellipsis)
    _second: _Operand = _get

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


@documenting_by(
    """
    Function to create a function by insertion its input action in the input
    template.

    The created function replaces `...` with an input action.
    """
)
@func
def binding_by(
    template: Iterable[Callable | Ellipsis],
) -> Callable[[Callable], ActionChain]:
    @documenting_by(
        """
        Function given as a result of calling `binding_by`. See `binding_by`
        for more info.
        """
    )
    @func
    def insert_to_template(intercalary_action: Callable) -> ActionChain:
        return ActionChain(
            intercalary_action if action is Ellipsis else action
            for action in template
        )

    return insert_to_template


atomic_binding_by: LeftCallable[
    Iterable[Callable | Ellipsis],
    Callable[Callable, Callable],
]
atomic_binding_by = documenting_by(
    """`binding_by` linking actions to an indivisible `ActionChain`."""
)(func(
    binding_by |then>> binding_by(... |then>> func)
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
)(func(
    will(map)
    |then>> binding_by(
        on(rpartial(isinstance, ActionChain) |then>> not_, lambda v: (v, ))
        |then>> ...
        |then>> ActionChain
    )
    |then>> func
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
