from functools import partial, cached_property
from inspect import Parameter
from typing import Any, Self, Optional, Callable

from act.annotations import Pm, R, Special
from act.atomization import fun
from act.representations import code_like_repr_of, ActionReprMixnin
from act.signatures import call_signature_of
from act.tools import documenting_by, Decorator


__all__ = (
    "partial",
    "partially",
    "flipped",
    "mirrored_partial",
    "rpartial",
    "will",
    "rwill",
)


class partial(partial):
    """Decorator to partially apply an input action on input arguments."""

    def __repr__(self) -> str:
        return f"partial({code_like_repr_of(self.func)}{{}}{{}}{{}}{{}})".format(
            ', ' if self.args or self.keywords else str(),
            f"{', '.join(map(code_like_repr_of, self.args))}",
            ', ' if self.args and self.keywords else str(),
            ', '.join(
                f"{key}={code_like_repr_of(arg)}"
                for key, arg in self.keywords.items()
            ),
        )


class _Partially(ActionReprMixnin):
    _repr_prefix = "partially"

    def __init__(self, action: Callable[Pm, R], required: Optional[int] = None):
        self._action = action
        self.__force_required = required

    @cached_property
    def _required(self) -> int:
        required = self.__force_required
        del self.__force_required

        if required is not None:
            return required

        return _required_number_of(self._action)

    def __call__(self, *args, **kwargs) -> Any | Self:
        partial_applied_action = partial(self._action, *args, **kwargs)

        if _required_number_of(partial_applied_action) == 0:
            return partial_applied_action()

        return _Partially(partial_applied_action, self._required - len(args))


def partially(action: Optional[Callable] = None, *, required: Optional[int] = None):
    """
    Decorator for splitting a decorated action call into non-structured
    sub-calls.

    Each sub-call adds arguments, as long as their number does not exceed the
    required ones. After filling, the action is called with these arguments.

    On each sub-call returns a decorated action with padded arguments.

    Required arguments are those that are not specified by keyword and do not
    have a default value.
    """

    return (
        partial(partially, required=required)
        if action is None
        else _Partially(action, required)
    )


@documenting_by(
    """Decorator to mirror positional parameters without default value."""
)
@fun
class flipped(Decorator):
    def __call__(self, *args, **kwargs) -> R:
        return self._action(*args[::-1], **kwargs)


def mirrored_partial(action: Callable[..., R], *args, **kwargs) -> Callable[..., R]:
    """
    Function to partially apply an input action with mirrored parameters by
    input arguments.
    """

    return flipped(partial(flipped(action), *args, **kwargs))


def rpartial(action: Callable[..., R], *args, **kwargs) -> Callable[..., R]:
    """
    Function similar to `functools.partial` with the difference that partially
    applied arguments are set not to the left but to the right.
    """

    return mirrored_partial(action, *args[::-1], **kwargs)


def will(action: Callable[..., R]) -> Callable[..., Callable[..., R]]:
    """
    to represent an input action into an action that partially applies
    that input action like `partial` function.
    """

    return partial(partial, action)


def rwill(action: Callable[..., R]) -> Callable[..., Callable[..., R]]:
    """
    Decorator to represent an input action into an action that partially applies
    that input action like `rpartial` function.
    """

    return partial(rpartial, action)


def _required_number_of(value: Special[Callable]) -> int:
    parameters = call_signature_of(value).parameters.values()

    return len(tuple(filter(_is_required, parameters)))


def _is_required(parameter: Parameter) -> bool:
    """Function that determines whether a parameter is required to be called."""

    valid_kinds = (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)

    return parameter.kind in valid_kinds and parameter.default is Parameter.empty
