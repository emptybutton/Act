from typing import Iterable, Generator, Optional, Callable, Type

from pyannotating import Special

from pyhandling.annotations import dirty, V, R
from pyhandling.atomization import atomically
from pyhandling.data_flow import eventually, by, to
from pyhandling.error_flow import catching
from pyhandling.pipeline import binding_by, then, on
from pyhandling.synonyms import trying_to, returned
from pyhandling.tools import documenting_by, LeftCallable


__all__ = (
    "iteration_over",
    "infinite",
    "times",
)


iteration_over: LeftCallable[Iterable[V], LeftCallable[..., Optional[V]]]
iteration_over = documenting_by(
    """
    Decorator to atomically iterate over an input iterable object via call.
    When `StopIteration` occurs, returns it.
    """
)(
    atomically(
        iter
        |then>> (eventually |to| next)
        |then>> (trying_to |by| to(catching(StopIteration, returned)))
    )
)


infinite: LeftCallable[
    Callable[V, Special[Type[StopIteration], R]],
    Callable[V, Optional[R]],
]
infinite = documenting_by(
    """Decorator function to return `None` instead of `StopIteration`."""
)(
    binding_by(... |then>> on(isinstance |by| StopIteration, None))
    |then>> atomically
)


@dirty
@documenting_by(
    """
    Function for a function returning `True` an input number of times, then
    `False` once, and again.

    Return function ignores its input arguments.
    """
)
@atomically
@binding_by(... |then>> iteration_over)
def times(max_steps: int, /) -> Generator[bool, None, None]:
    steps = max_steps

    while True:
        yield steps > 0
        steps -= 1

        if steps < 0:
            steps = max_steps
