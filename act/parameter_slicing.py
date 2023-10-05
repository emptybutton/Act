from functools import reduce
from typing import Iterable, Callable, Tuple, Self

from act.annotations import Pm, R, D
from act.data_flow import by
from act.representations import code_like_repr_of
from act.structures import flat
from act.tools import items_of


__all__ = ("take", )


def _indexer_repr_of(points: Iterable) -> str:
    points = tuple(points)

    return (
        reduce(
            lambda line, point: f"{line}[{code_like_repr_of(point)}]",
            (str(), *points),
        )
        if len(points) > 0
        else str()
    )


class _ArgumentSlicer:
    def __init__(
        self,
        name: str,
        *,
        positions: Iterable[int | slice] = tuple(),
        keywords: Iterable[str] = tuple(),
        decorator: Callable[[Callable[Pm, R], Tuple[int | slice], Tuple[str]], D],
    ):
        self._name = name
        self._positions = tuple(positions)
        self._keywords = tuple(keywords)
        self._decorator = decorator

    def __repr__(self) -> str:
        return f"{self._name}{{}}".format(
            _indexer_repr_of((*self._positions, *self._keywords)),
        )

    def __getitem__(
        self,
        taken: int | slice | str | tuple[int | slice | str],
    ) -> Self:
        items = items_of(taken)

        return type(self)(
            self._name,
            decorator=self._decorator,
            keywords=(*self._keywords, *filter(isinstance |by| str, items)),
            positions=(
                *self._positions,
                *filter(isinstance |by| (int | slice), items)
            ),
        )

    def __call__(self, action: Callable[Pm, R]) -> D:
        return self._decorator(action, self._positions, self._keywords)


class _IgnoringCallable:
    def __init__(
        self,
        action: Callable[Pm, R],
        poisitions: Iterable[int | slice],
        keywords: Iterable[str],
    ):
        self._action = action
        self._poisitions = tuple(poisitions)
        self._keywords = tuple(keywords)

    def __repr__(self) -> str:
        points = (*self._poisitions, *self._keywords)

        return f"take{_indexer_repr_of(points)}({code_like_repr_of(self._action)})"

    def __call__(self, *args, **kwargs) -> R:
        return self._action(
            *flat(args[position] for position in self._poisitions),
            **{
                keyword: _ for keyword, _ in kwargs.items()
                if keyword in self._keywords
            },
        )


take = _ArgumentSlicer("take", decorator=_IgnoringCallable)
