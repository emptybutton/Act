from functools import wraps, partial
from typing import Callable, TypeVar, Any

from pyhandling.annotations import ResultT, ActionT, ArgumentsT, event_for, action_for
from pyhandling.tools import ArgumentKey, ArgumentPack


__all__ = (
    "post_partial", "mirror_partial", "closed", "returnly", "eventually", "unpackly"
)


def post_partial(action: Callable[[...], ResultT], *args, **kwargs) -> Callable[[...], ResultT]:
    """
    Function equivalent to functools.partial but with the difference that
    additional arguments are added not before the incoming ones from the final
    call, but after.
    """

    @wraps(action)
    def wrapper(*wrapper_args, **wrapper_kwargs) -> ResultT:
        return action(*wrapper_args, *args, **wrapper_kwargs, **kwargs)

    return wrapper


def mirror_partial(action: Callable[[...], ResultT], *args, **kwargs) -> Callable[[...], ResultT]:
    """
    Function equivalent to pyhandling.handlers.post_partial but with the
    difference that additional arguments from this function call are unfolded.
    """

    return post_partial(action, *args[::-1], **kwargs)


ClosedT = TypeVar("ClosedT", bound=Callable)


def closed(
    action: ActionT,
    *,
    closer: Callable[[ActionT, *ArgumentsT], ClosedT] = partial
) -> Callable[[*ArgumentsT], ClosedT]:
    """
    Function to put an input function into the context of another decorator
    function by partially applying the input function to that decorator
    function.

    The decorator function is defined by the `closer` parameter.

    On default `closer` value wraps the input function in a function whose
    result is the same input function, but partially applied with the arguments
    with which the resulting function was called.

    ```
    closed(print)(1, 2)(3) # 1 2 3
    ```
    """

    return partial(closer, action)


def returnly(
    action: Callable[[*ArgumentsT], Any],
    *,
    argument_key_to_return: ArgumentKey = ArgumentKey(0)
) -> Callable[[*ArgumentsT], ArgumentsT]:
    """
    Decorator function that causes the input function to return not the result
    of its execution, but some argument that is incoming to it.

    Returns the first argument by default.
    """

    @wraps(action)
    def wrapper(*args, **kwargs) -> Any:
        action(*args, **kwargs)

        return ArgumentPack(args, kwargs)[argument_key_to_return]

    return wrapper


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