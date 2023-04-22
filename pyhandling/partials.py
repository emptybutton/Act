from collections import OrderedDict
from functools import cached_property, partial
from inspect import Parameter, Signature, _empty
from typing import Any, Self, Iterable, Tuple, Optional

from pyhandling.annotations import action_for, ResultT
from pyhandling.atoming import atomically
from pyhandling.signature_assignmenting import Decorator, call_signature_of


__all__ = (
    "fragmentarily",
    "flipped",
    "mirrored_partial",
    "rpartial",
    "will",
    "rwill",
)


@atomically
class fragmentarily(Decorator):
    """
    Decorator for splitting a decorated action call into non-structured
    sub-calls.

    Each sub-call adds arguments, as long as their number does not exceed the
    required ones. After filling, the action is called with these arguments.

    On each sub-call returns a decorated action with padded arguments.

    Required arguments are those that are not specified by keyword and do not
    have a default value.
    """

    def __call__(self, *args, **kwargs) -> Any | Self:
        augmented_action = partial(self._action, *args, **kwargs)

        actual_parameters_to_call = OrderedDict(
            tuple(
                (parameter_name, parameter)
                for parameter_name, parameter in self._parameters_to_call.items()
                if (
                    parameter_name not in kwargs.keys()
                    and parameter.default is _empty
                )
            )[len(args):]
        )

        return (
            augmented_action()
            if len(actual_parameters_to_call) == 0
            else fragmentarily(augmented_action)
        )

    @cached_property
    def _parameters_to_call(self) -> OrderedDict[str, Parameter]:
        return OrderedDict(
            (_, parameter)
            for _, parameter in (
                call_signature_of(self._action).parameters.items()
            )
            if _is_parameter_settable(parameter)
        )

    @cached_property
    def _force_signature(self) -> Signature:
        return call_signature_of(self).replace(
            return_annotation=(
                call_signature_of(self._action).return_annotation | Self,
            ),
            parameters=tuple(
                (
                    parameter.replace(
                        default=None, annotation=Optional[parameter.annotation]
                    )
                    if _is_parameter_settable(parameter)
                    else parameter
                )
                for parameter in (
                    call_signature_of(self._action).parameters.values()
                )
            )
        )


@atomically
class flipped(Decorator):
    """Decorator to mirror positional parameters without default value."""

    def __call__(self, *args, **kwargs) -> ResultT:
        return self._action(*args[::-1], **kwargs)

    @cached_property
    def _force_signature(self) -> Signature:
        return call_signature_of(self._action).replace(
            parameters=self.__flip_parameters(
                call_signature_of(self._action).parameters.values()
            )
        )

    @staticmethod
    def __flip_parameters(parameters: Iterable[Parameter]) -> Tuple[Parameter]:
        parameters = tuple(parameters)
        index_border_to_invert = 0

        for parameter_index, parameter in enumerate(parameters):
            if not _is_parameter_settable(parameter):
                break

            index_border_to_invert = parameter_index

        return (
            *parameters[index_border_to_invert::-1],
            *parameters[index_border_to_invert + 1:],
        )


def mirrored_partial(
    action: action_for[ResultT],
    *args,
    **kwargs,
) -> action_for[ResultT]:
    """
    Function to partially apply input action with mirrored parameters by input
    arguments.
    """

    return flipped(partial(flipped(action), *args, **kwargs))


def rpartial(action: action_for[ResultT], *args, **kwargs) -> action_for[ResultT]:
    """
    Function similar to `functools.partial` with the difference that partially
    applied arguments are set not to the left but to the right.
    """

    return mirrored_partial(action, *args[::-1], **kwargs)


def will(action: action_for[ResultT]) -> action_for[action_for[ResultT]]:
    """
    Decorator to represent an input action into an action that partially applies
    that input action like `partial` function.
    """

    return partial(partial, action)


def rwill(action: action_for[ResultT]) -> action_for[action_for[ResultT]]:
    """
    Decorator to represent an input action into an action that partially applies
    that input action like `rpartial` function.
    """

    return partial(rpartial, action)


def _is_parameter_settable(parameter: Parameter) -> bool:
    """Function that determines whether a parameter is required to be called."""
    
    return (
        parameter.default is _empty
        and parameter.kind in (
            Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD
        )
    )
