from typing import Optional, Self, Type


class MockObject:
    def __init__(self, **attributes):
        self.__dict__ = attributes

    def __repr__(self) -> str:
        return "<MockObject with {attributes}>".format(
            attributes=str(self.__dict__)[1:-1].replace(': ', '=').replace('\'', '')
        )


class Box(MockObject):
    def __init__(self, enter_result: any = None, **attributes):
        super().__init__(**attributes)
        self.enter_result = enter_result

    def __repr__(self) -> str:
        return '<Box instance>'

    def __enter__(self) -> any:
        return self.enter_result

    def __exit__(self, error_type: Optional[Type[Exception]], error: Optional[Exception], traceback: any):
        pass


class MockHandler:
    def __init__(self, equality_id: Optional[int] = None):
        self.equality_id = equality_id

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return "<MockHandler>"

    def __call__(self, resource: any) -> any:
        return resource

    def __eq__(self, other: Self) -> bool:
        return (
            self is other
            if self.equality_id is None
            else self.equality_id == other.equality_id
        )


class Counter:
    def __init__(self, counted: int = 0):
        self._counted = counted

    @property
    def counted(self) -> int:
        return self._counted

    def __repr__(self) -> str:
        return f"Counter({self._counted})"

    def __call__(self, number_of_counts: int = 1) -> None:
        self._counted += number_of_counts