from typing import Any, Optional, Type, NoReturn

from pytest import fail


class CustomContext:
    """Class emulating context."""
    
    def __init__(self, enter_result: Any = None):
        self.enter_result = enter_result

    def __repr__(self) -> str:
        return "<CustomContext instance>"

    def __enter__(self) -> Any:
        return self.enter_result

    def __exit__(self, error_type: Optional[Type[Exception]], error: Optional[Exception], traceback: Any):
        pass


class MockAction:
    """
    Mock action without action. Returns input resource.
    Optionally compared with another by input id.
    """

    def __init__(self, equality_id: Optional[int] = None):
        self.equality_id = equality_id

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return "<MockHandler>"

    def __call__(self, resource: Any) -> Any:
        return resource

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MockAction) and (
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


def fail_by_error(error: Exception) -> NoReturn:
    fail(f"Catching the unexpected error {error.__class__.__name__} \"{str(error)}\"")