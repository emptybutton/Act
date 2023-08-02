from typing import Iterable, Optional, Callable, Type

from pyannotating import Special

from act.annotations import V, R
from act.atomization import atomically
from act.data_flow import eventually, by, to
from act.error_flow import catch
from act.pipeline import binding_by, then, on
from act.synonyms import try_
from act.tools import documenting_by, LeftCallable, _get


__all__ = (
    "iteration_over",
    "infinite",
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
        |then>> (try_ |by| to(catch(StopIteration, _get)))
    )
)


infinite: LeftCallable[
    Callable[V, Special[Type[StopIteration], R]],
    LeftCallable[V, Optional[R]],
]
infinite = documenting_by(
    """Decorator function to return `None` instead of `StopIteration`."""
)(
    binding_by(... |then>> on(isinstance |by| StopIteration, None))
    |then>> atomically
)
