from typing import Any, Optional, Self, Type


class _AttributeKeeper:
    """Mock class having dynamic attributes."""

    def __init__(self, **attributes):
        self.__dict__ = attributes

    def __repr__(self) -> str:
        return "<_AttributeKeeper with {attributes}>".format(
            attributes=str(self.__dict__)[1:-1].replace(': ', '=').replace('\'', '')
        )


class MockError(MockObject, Exception):
    pass


class Box(MockObject):
    """MockObject class emulating context."""
    
    def __init__(self, enter_result: Any = None, **attributes):
        super().__init__(**attributes)
        self.enter_result = enter_result

    def __repr__(self) -> str:
        return '<Box instance>'

    def __enter__(self) -> Any:
        return self.enter_result

    def __exit__(self, error_type: Optional[Type[Exception]], error: Optional[Exception], traceback: Any):
        pass


class MockHandler:
    """
    Mock class creating a handling effect by returning an input resource.

    Has an additional identification when specifying equality_id, allowing you
    to compare this handlers by this very id.
    """

    def __init__(self, equality_id: Optional[int] = None):
        self.equality_id = equality_id

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return "<MockHandler>"

    def __call__(self, resource: Any) -> Any:
        return resource

    def __eq__(self, other: Self) -> bool:
        return (
            self is other
            if self.equality_id is None
            else self.equality_id == other.equality_id
        )


class Counter:
    """Counter class that counts its calls."""

    def __init__(self, counted: int = 0):
        self._counted = counted

    @property
    def counted(self) -> int:
        return self._counted

    def __repr__(self) -> str:
        return f"Counter({self._counted})"

    def __call__(self, number_of_counts: int = 1) -> None:
        self._counted += number_of_counts