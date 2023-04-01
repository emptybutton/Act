from abc import ABC, abstractmethod
from collections import OrderedDict
from functools import partial, wraps, update_wrapper, cached_property
from inspect import signature, _empty, Signature, Parameter
from typing import Callable, Self, TypeVar, Any, Iterable, NamedTuple, Tuple, Generic, Optional

from pyhandling.annotations import ArgumentsT, ResultT, action_for, ActionT, handler_of
from pyhandling.errors import ReturningError
from pyhandling.synonyms import with_keyword
from pyhandling.tools import ArgumentKey, ArgumentPack


__all__ = (
    "flipped",
    "fragmentarily",
    "post_partial",
    "mirror_partial",
    "closed",
    "returnly",
    "eventually",
    "unpackly",
)


class _FunctionWrapper(ABC, Generic[ActionT]):
    def __init__(self, action: ActionT):
        self._action = action
        self._become_native()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._action})"

    @property
    @abstractmethod
    def _native_signature(self) -> Signature:
        ...

    def _become_native(self) -> None:
        update_wrapper(self, self._action)
        self.__signature__ = self._native_signature

        if hasattr(self._action, "__name__"):
            self.__name__ = f"{type(self).__name__}({self._action.__name__})"


class flipped(_FunctionWrapper):
    def __call__(self, *args, **kwargs) -> ResultT:
        return self._action(*args[::-1], **kwargs)

    @cached_property
    def _native_signature(self) -> Signature:
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


class returnly(_FunctionWrapper):
    """
    Decorator that causes the input function to return not the result of its
    execution, but some argument that is incoming to it.

    Returns the first argument by default.
    """

    def __call__(self, *args, **kwargs) -> ArgumentsT:
        self._action(*args, **kwargs)

        return args[0]

    @cached_property
    def _native_signature(self) -> Signature:
        parameters = tuple(signature(self._action).parameters.values())

        if len(parameters) == 0:
            raise ReturningError("Function must contain at least one parameter")

        return signature(self._action).replace(return_annotation=(
            parameters[0].annotation
        ))


class eventually(_FunctionWrapper):
    """
    Decorator function to call with predefined arguments instead of input ones.
    """

    def __init__(self, action: Callable[[*ArgumentsT], ResultT], *args: ArgumentsT, **kwargs: ArgumentsT):
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
    def _native_signature(self) -> Signature:
        return signature(self._action).replace(parameters=tuple())


class unpackly(_FunctionWrapper):
    """
    Decorator function to unpack the input `ArgumentPack` into the input function.
    """

    def __call__(self, pack: ArgumentPack) -> Any:
        return pack.call(self._action)

    @cached_property
    def _native_signature(self) -> Signature:
        return signature(self).replace(
            return_annotation=signature(self._action).return_annotation
        )


class fragmentarily(_FunctionWrapper):
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
            for _, parameter in signature(self._action).parameters.items()
            if self.__is_parameter_settable(parameter)
        )

    @cached_property
    def _native_signature(self) -> Signature:
        return signature(self).replace(
            return_annotation=signature(self._action).return_annotation | Self,
            parameters=tuple(
                (
                    parameter.replace(
                        default=None, annotation=Optional[parameter.annotation]
                    )
                    if self.__is_parameter_settable(parameter)
                    else parameter
                )
                for parameter in signature(self._action).parameters.values()
            )
        )

    def __is_parameter_settable(self, parameter: Parameter) -> bool:
        return (
            parameter.default is _empty
            and parameter.kind in (
                Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD
            )
        )


def post_partial(action: action_for[ResultT], *args, **kwargs) -> action_for[ResultT]:
    """
    Function equivalent to functools.partial but with the difference that
    additional arguments are added not before the incoming ones from the final
    call, but after.
    """

    return flipped(partial(flipped(action), *args[::-1], **kwargs))


def mirror_partial(action: action_for[ResultT], *args, **kwargs) -> action_for[ResultT]:
    """
    Function equivalent to pyhandling.handlers.post_partial but with the
    difference that additional arguments from this function call are unfolded.
    """

    return post_partial(action, *args[::-1], **kwargs)


_ClosedT = TypeVar("_ClosedT", bound=Callable)


def closed(
    action: ActionT,
    *,
    close: Callable[[ActionT, *ArgumentsT], _ClosedT] = partial
) -> Callable[[*ArgumentsT], _ClosedT]:
    """
    Function to put an input function into the context of another decorator
    function by partially applying the input function to that decorator
    function.

    The decorator function is defined by the `close` parameter.

    On default `close` value wraps the input function in a function whose
    result is the same input function, but partially applied with the arguments
    with which the resulting function was called.

    ```
    closed(print)(1, 2)(3) # 1 2 3
    ```
    """

    return partial(close, action)