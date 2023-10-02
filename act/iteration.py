from typing import Iterable, Optional, Callable, Type

from pyannotating import Special

from act.annotations import V, R
from act.atomization import fun
from act.data_flow import eventually, by, to
from act.error_flow import catch
from act.pipeline import bind_by, then, on
from act.synonyms import try_
from act.tools import documenting_by, _get


__all__ = (
    "iteration_over",
    "infinite",
)


iteration_over: Callable[Iterable[V], Callable[..., Optional[V]]]
iteration_over = documenting_by(
    """
    Decorator to atomically iterate over an input iterable object via call.
    When `StopIteration` occurs, returns it.
    """
)(
    fun(
        iter
        |then>> (eventually |to| next)
        |then>> (try_ |by| to(catch(StopIteration, _get)))
    )
)


infinite: Callable[
    Callable[V, Special[Type[StopIteration], R]],
    Callable[V, Optional[R]],
]
infinite = documenting_by(
    """Decorator function to return `None` instead of `StopIteration`."""
)(
    bind_by(... |then>> on(isinstance |by| StopIteration, None))
    |then>> fun
)
