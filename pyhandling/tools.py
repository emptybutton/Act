from dataclasses import dataclass, field
from typing import Iterable, Self, Callable


@dataclass(frozen=True)
class Arguments:
    args: Iterable = tuple()
    kwargs: dict = field(default_factory=dict)

    def clone_with(self, *args, **kwargs) -> Self:
        return self.__class__(
            (*self.args, *args),
            self.kwargs | kwargs
        )

    def merge_clone_with(self, arguments: Self) -> Self:
        return self.__class__(
            (*self.args, *arguments.args),
            self.kwargs | arguments.kwargs
        )

    def call(self, caller: Callable) -> any:
        return caller(*self.args, **self.kwargs)

    @classmethod
    def create_via_call(cls, *args, **kwargs) -> Self:
        return cls(args, kwargs)


