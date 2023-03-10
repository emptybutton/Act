from functools import wraps, partial
from typing import Callable, Any

from pyhandling.annotations import ActionT, ResourceT, ResultT, event_for
from pyhandling.tools import ArgumentPack


__all__ = ("post_partial", "mirror_partial", "close", "unpackly")


def post_partial(func: FuncT, *args, **kwargs) -> FuncT:
    """
    Function equivalent to functools.partial but with the difference that
    additional arguments are added not before the incoming ones from the final
    call, but after.
    """

    @wraps(func)
    def wrapper(*wrapper_args, **wrapper_kwargs) -> Any:
        return func(*wrapper_args, *args, **wrapper_kwargs, **kwargs)

    return wrapper


def mirror_partial(func: Callable, *args, **kwargs) -> Callable:
    """
    Function equivalent to pyhandling.handlers.rigth_partial but with the
    difference that additional arguments from this function call are unfolded.
    """

    return post_partial(action, *args[::-1], **kwargs)


def close(resource: ResourceT, *, closer: Callable[[ResourceT, ...], ResultT] = partial) -> event_for[ResultT]:
    """
    Function to create a closure for the input resource.

    Wraps the input resource in a container function that can be \"opened\" when
    that function is called.

    The input resource type depends on the chosen closer function.

    With a default closer function, ***it requires a Callable resource***.

    When \"opened\" the default container function returns an input resource with
    the bined input arguments from the function container.
    """

    return partial(closer, resource)


def unpackly(func: event_for[ResultT]) -> Callable[[ArgumentPack], ResultT]:
    """
    Decorator function that allows to bring an ordinary function to the handler
    interface by unpacking the input argument pack into the input function.
    """

    return wraps(func)(lambda pack: pack.call(func))