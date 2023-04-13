from collections import OrderedDict
from functools import cached_property, partial
from inspect import Parameter, Signature, _empty
from typing import Any, Self, Iterable, Tuple, Optional

from pyhandling.annotations import action_for, ResultT
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of


__all__ = (
    "fragmentarily",
    "flipped",
    "mirrored_partial",
    "right_partial",
    "will",
    "rwill",
)


class fragmentarily(ActionWrapper):
    """
    Decorator for splitting a decorated function call into non-structured
    sub-calls.

    Partially binds subcall arguments to a decorated function using the `binder`
    parameter.
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
            for _, parameter in calling_signature_of(self._action).parameters.items()
            if _is_parameter_settable(parameter)
        )

    @cached_property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self).replace(
            return_annotation=calling_signature_of(self._action).return_annotation | Self,
            parameters=tuple(
                (
                    parameter.replace(
                        default=None, annotation=Optional[parameter.annotation]
                    )
                    if _is_parameter_settable(parameter)
                    else parameter
                )
                for parameter in calling_signature_of(self._action).parameters.values()
            )
        )


class flipped(ActionWrapper):
    def __call__(self, *args, **kwargs) -> ResultT:
        return self._action(*args[::-1], **kwargs)

    @cached_property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(
            parameters=self.__flip_parameters(
                calling_signature_of(self._action).parameters.values()
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


def mirrored_partial(action: action_for[ResultT], *args, **kwargs) -> action_for[ResultT]:
    """
    Function equivalent to pyhandling.handlers.right_partial but with the
    difference that additional arguments from this function call are unfolded.
    """

    return flipped(partial(flipped(action), *args, **kwargs))


def right_partial(action: action_for[ResultT], *args, **kwargs) -> action_for[ResultT]:
    """
    Function equivalent to functools.partial but with the difference that
    additional arguments are added not before the incoming ones from the final
    call, but after.
    """

    return mirrored_partial(action, *args[::-1], **kwargs)


def will(action: action_for[ResultT]) -> action_for[action_for[ResultT]]:
    return partial(partial, action)


def rwill(action: action_for[ResultT]) -> action_for[action_for[ResultT]]:
    return partial(right_partial, action)


def _is_parameter_settable(parameter: Parameter) -> bool:
    return (
        parameter.default is _empty
        and parameter.kind in (
            Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD
        )
    )