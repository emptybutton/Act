from dataclasses import dataclass

from pyhandling.annotations import O, P, V, G, S, A, B


__all__ = (
    "Access",
)


@dataclass(frozen=True)
class Access(Generic[O, P, V, G, S]):
    """Aggregate class of getter and setter functions."""
    
    get: Callable[[O, P], G]
    set: Callable[[O, P, V], S]

