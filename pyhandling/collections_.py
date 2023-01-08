from typing import Container, Iterable, Self, Generator


class NonInclusiveCollection:
    """Class that explicitly stores entities that are not stored in it."""

    def __init__(self, elements_not_contained: Container):
        self.elements_not_contained = elements_not_contained

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(all except {self.elements_not_contained})"

    def __contains__(self, item: any) -> bool:
        return not item in self.elements_not_contained


class MultiRange:
    """
    Class containing ranges to provide them as one object.

    Delegates iteration and containing to its ranges.
    You can also create a new Multirange based on an old one with ranges, range
    or another Multirange using the \"|\" operator (or get_with method) on the
    desired resource.
    """

    def __init__(self, range_resource: Iterable[range] | range):
        self._ranges = (
            (range_resource, )
            if isinstance(range_resource, range)
            else tuple(range_resource)
        )

    @property
    def ranges(self) -> tuple[range]:
        return self._ranges

    def get_with(self, range_resource: Self | Iterable[range] | range) -> Self:
        """Method that implements getting a new Multirange with additional ranges."""

        if isinstance(range_resource, MultiRange):
            range_resource = range_resource.ranges

        if isinstance(range_resource, range):
            range_resource = (range_resource, )

        return self.__class__(self.ranges + tuple(range_resource))

    def __repr__(self) -> str:
        return "MultiRange({})".format(', '.join(map(str, self.ranges)))

    def __iter__(self) -> iter:
        return (
            item
            for range_ in self.ranges
            for item in range_
        )

    def __contains__(self, item: any) -> bool:
        return any(
            item in range_
            for range_ in self.ranges
        )

    def __or__(self, range_resource: Self | Iterable[range] | range) -> Self:
        return self.get_with(range_resource)


class Combination:
    def __init__(self, *elements: any):
        self.elements = elements

    def __repr__(self) -> str:
        return (
            f"<Combination of {list(self.elements)}>"
            if len(self.elements)
            else "<Neutral Combination>"
        )

    def __iter__(self) -> Generator[tuple, None, None]:
        if len(self.elements) <= 1:
            yield from self.elements

        current_collection = tuple(self.elements)

        for _ in range(len(self.elements)):
            for swipe_element_index in range(1, len(self.elements)):
                current_collection = tuple( 
                    {
                        swipe_element_index - 1: current_collection[swipe_element_index],
                        swipe_element_index: current_collection[swipe_element_index - 1]
                    }.get(element_index, element)
                    for element_index, element in enumerate(current_collection)
                )

                yield current_collection