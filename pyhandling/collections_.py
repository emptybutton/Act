from typing import Container, Any, Tuple, Self, Generator

from pyannotating import many_or_one


__all__ = ("NonInclusiveCollection", "MultiRange")


class NonInclusiveCollection:
    """Class that explicitly stores entities that are not stored in it."""

    def __init__(self, elements_not_contained: Container):
        self.elements_not_contained = elements_not_contained

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(all except {self.elements_not_contained})"

    def __contains__(self, item: Any) -> bool:
        return not item in self.elements_not_contained


class MultiRange:
    """
    Class containing ranges to provide them as one object.

    Delegates iteration and containing to its ranges.
    You can also create a new Multirange based on an old one with ranges, range
    or another Multirange using the \"|\" operator (or get_with method) on the
    desired resource.
    """

    def __init__(self, range_resource: many_or_one[range]):
        self._ranges = (
            (range_resource, )
            if isinstance(range_resource, range)
            else tuple(range_resource)
        )

    @property
    def ranges(self) -> Tuple[range]:
        return self._ranges

    def get_with(self, range_resource: Self | many_or_one[range]) -> Self:
        """Method that implements getting a new Multirange with additional ranges."""

        if isinstance(range_resource, MultiRange):
            range_resource = range_resource.ranges

        if isinstance(range_resource, range):
            range_resource = (range_resource, )

        return self.__class__(self.ranges + tuple(range_resource))

    def __repr__(self) -> str:
        return "MultiRange({})".format(', '.join(map(str, self.ranges)))

    def __iter__(self) -> Generator[int, None, None]:
        return (
            item
            for range_ in self.ranges
            for item in range_
        )

    def __contains__(self, item: Any) -> bool:
        return any(
            item in range_
            for range_ in self.ranges
        )

    def __or__(self, range_resource: Self | many_or_one[range]) -> Self:
        return self.get_with(range_resource)
