from abc import ABC, abstractmethod
from collections import OrderedDict
from functools import partial, wraps, update_wrapper, cached_property
from inspect import signature, _empty, Signature, Parameter
from typing import Callable, Self, TypeVar, Any, Iterable, NamedTuple, Tuple, Generic, Optional

from pyhandling.annotations import ArgumentsT, ResultT, action_for, ActionT, handler_of
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


def fragmentarily(action: Callable[[*ArgumentsT], ResultT]) -> action_for[ResultT | Self]:
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


    """
    Function decorator for splitting a decorated function call into
    non-structured sub-calls.

    Partially binds subcall arguments to a decorated function using the `binder`
    parameter.
    """

    parameters_to_call = OrderedDict(
        (_, parameter)
        for _, parameter in signature(action).parameters.items()
        if (
            parameter.kind in (
                _ParameterKind.POSITIONAL_ONLY,
                _ParameterKind.POSITIONAL_OR_KEYWORD
            )
            and parameter.default is _empty
        )
    )

    @wraps(action)
    def fragmentarily_action(*args, **kwargs) -> ResultT | Self:
        augmented_action = partial(action, *args, **kwargs)

        actual_parameters_to_call = OrderedDict(
            tuple(
                (parameter_name, parameter)
                for parameter_name, parameter in parameters_to_call.items()
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

    return fragmentarily_action


def post_partial(action: action_for[ResultT], *post_args, **post_kwargs) -> action_for[ResultT]:
    """
    Function equivalent to functools.partial but with the difference that
    additional arguments are added not before the incoming ones from the final
    call, but after.
    """

    return wraps(action)(
        lambda *args, **kwargs: action(*args, *post_args, **post_kwargs, **kwargs)
    )


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


def returnly(
    action: handler_of[*ArgumentsT],
    *,
    argument_key_to_return: ArgumentKey = ArgumentKey(0)
) -> Callable[[*ArgumentsT], ArgumentsT]:
    """
    Decorator function that causes the input function to return not the result
    of its execution, but some argument that is incoming to it.

    Returns the first argument by default.
    """

    @wraps(action)
    def returnly_action(*args, **kwargs) -> Any:
        action(*args, **kwargs)

        return ArgumentPack(args, kwargs)[argument_key_to_return]

    return returnly_action


def eventually(action: action_for[ResultT], *args, **kwargs) -> action_for[ResultT]:
    """
    Decorator function to call with predefined arguments instead of input ones.
    """

    return wraps(action)(lambda *_, **__: action(*args, **kwargs))


def unpackly(action: action_for[ResultT]) -> Callable[[ArgumentPack], ResultT]:
    """
    Decorator function to unpack the input `ArgumentPack` into the input function.
    """

    return wraps(action)(lambda pack: pack.call(action))