from typing import Container, Generator, Iterable, Self


class NonInclusiveCollection:
    """Class that explicitly stores entities that are not stored in it."""

    def __init__(self, elements_not_contained: Container):
        self.elements_not_contained = elements_not_contained

    def __contains__(self, item: any) -> bool:
        return not item in self.elements_not_contained
