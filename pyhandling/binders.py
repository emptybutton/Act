from functools import wraps, partial
from typing import Callable, Iterable

from pyhandling.annotations import handler_of
from pyhandling.tools import ArgumentPack


def post_partial(func: Callable, *args, **kwargs) -> Callable:
    """
    Function equivalent to functools.partial but with the difference that
    additional arguments are added not before the incoming ones from the final
    call, but after.
    """

    @wraps(func)
    def wrapper(*wrapper_args, **wrapper_kwargs) -> any:
        return func(*wrapper_args, *args, **wrapper_kwargs, **kwargs)

    return wrapper


def mirror_partial(func: Callable, *args, **kwargs) -> Callable:
    """
    Function equivalent to pyhandling.handlers.rigth_partial but with the
    difference that additional arguments from this function call are unfolded.
    """

    return rigth_partial(func, *args[::-1], **kwargs)


def bind(func: Callable, argument_name: str, argument_value: any) -> Callable:
    """
    Atomic partial function for a single keyword argument whose name and value
    are separate input arguments.
    """

    return wraps(func)(partial(func, **{argument_name: argument_value}))


def unpackly(func: Callable) -> handler_of[ArgumentPack | Iterable]:
    """
    Decorator function that allows to bring an ordinary function to the Handler
    interface by unpacking the input resource into the input function.

    Specifies the type of unpacking depending on the type of the input resource
    into the resulting function.

    When ArgumentPack delegates unpacking to it (Preferred Format).

    When a dict or otherwise a homogeneous collection unpacks * or **
    respectively.

    Also unpacks a collection of the form [collection, dict] as * and ** from
    this collection.
    """

    @wraps(func)
    def wrapper(argument_collection: ArgumentPack | Iterable) -> any:
        if isinstance(argument_collection, ArgumentPack):
            return argument_collection.call(func)
        elif isinstance(argument_collection, dict):
            return func(**argument_collection)
        elif isinstance(argument_collection, Iterable):
            return func(*argument_collection[0], **argument_collection[1]) if (
                len(argument_collection) == 2
                and isinstance(argument_collection[0], Iterable)
                and isinstance(argument_collection[1], dict)
            ) else func(*argument_collection)

    return wrapper


def close(resource: any, *, closer: Callable[[any, ...], any] = partial) -> Callable:
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