from abc import ABC, abstractmethod
from collections import OrderedDict
from functools import partial, wraps, update_wrapper, cached_property
from inspect import signature, _empty, Signature, Parameter
from typing import Callable, Self, TypeVar, Any, Iterable, NamedTuple, Tuple, Generic, Optional

from pyhandling.annotations import P, ValueT, ResultT, action_for, ActionT, handler_of
from pyhandling.errors import ReturningError
from pyhandling.tools import ActionWrapper, ArgumentKey, ArgumentPack, calling_signature_of


__all__ = (
    "returnly",
    "eventually",
    "unpackly",
    "fragmentarily",
    "flipped",
    "right_partial",
    "mirrored_partial",
    "closed",
    "right_closed",
)


class returnly(ActionWrapper):
    """
    Decorator that causes the input function to return not the result of its
    execution, but some argument that is incoming to it.

    Returns the first argument by default.
    """

    def __call__(self, value: ValueT, *args, **kwargs) -> ValueT:
        self._action(*args, **kwargs)

        return args[0]

    @cached_property
    def _force_signature(self) -> Signature:
        parameters = tuple(calling_signature_of(self._action).parameters.values())

        if len(parameters) == 0:
            raise ReturningError("Function must contain at least one parameter")

        return calling_signature_of(self._action).replace(return_annotation=(
            parameters[0].annotation
        ))


class eventually(ActionWrapper):
    """
    Decorator function to call with predefined arguments instead of input ones.
    """

    def __init__(self, action: Callable[P, ResultT], *args: P.args, **kwargs: P.kwargs):
        super().__init__(action)
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *_, **__) -> ResultT:
        return self._action(*self._args, **self._kwargs)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self._action}"
            f"{', ' if self._args or self._kwargs else str()}"
            f"{', '.join(map(str, self._args))}"
            f"{', ' if self._args and self._kwargs else str()}"
            f"{', '.join(map(lambda item: str(item[0]) + '=' + str(item[1]), self._kwargs.items()))})"
        )

    @cached_property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(parameters=(
            Parameter('_', Parameter.VAR_POSITIONAL, annotation=Any),
            Parameter('__', Parameter.VAR_KEYWORD, annotation=Any),
        ))


class unpackly(ActionWrapper):
    """
    Decorator function to unpack the input `ArgumentPack` into the input function.
    """

    def __call__(self, pack: ArgumentPack) -> Any:
        return pack.call(self._action)

    @cached_property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self).replace(
            return_annotation=signature(self._action).return_annotation
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
            if self.__is_parameter_settable(parameter)
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
                    if self.__is_parameter_settable(parameter)
                    else parameter
                )
                for parameter in calling_signature_of(self._action).parameters.values()
            )
        )

    def __is_parameter_settable(self, parameter: Parameter) -> bool:
        return (
            parameter.default is _empty
            and parameter.kind in (
                Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD
            )
        )


class flipped(ActionWrapper):
    def __call__(self, *args, **kwargs) -> ResultT:
        return self._action(*args[::-1], **kwargs)

    @cached_property
    def _force_signature(self) -> Signature:
        return signature(self._action).replace(parameters=self.__flip_parameters(
            signature(self._action).parameters.values()
        ))

    @staticmethod
    def __flip_parameters(parameters: Iterable[Parameter]) -> Tuple[Parameter]:
        parameters = tuple(parameters)
        index_border_to_invert = 0

        for parameter_index, parameter in enumerate(parameters):
            if parameter.default is not _empty:
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


def closed(action: action_for[ResultT]) -> action_for[action_for[ResultT]]:
    return partial(partial, action)


def right_closed(action: action_for[ResultT]) -> action_for[action_for[ResultT]]:
    return partial(right_partial, action)