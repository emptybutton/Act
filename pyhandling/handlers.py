from functools import reduce
from typing import NewType, Callable, Iterable, Self, Optional


Handler = NewType('Handler', Callable[[any], any])


class HandlerKeeper:
    def __init__(self, handler_resource: Handler | Iterable[Handler], *handlers: Handler):
        self.handlers = (
            tuple(handler_resource)
            if isinstance(handler_resource, Iterable)
            else (handler_resource, )
        ) + handlers


class MultipleHandler(HandlerKeeper):
    """
    Handler proxy class for representing multiple handlers as a single
    interface.

    Has the is_return_delegated flag attribute to enable or disable returning
    the result of one from the handlers.

    When one handler returns anything other than None, it returns that value,
    breaking the loop for other handlers.
    """

    def __init__(
        self,
        handler_resource: Handler | Iterable[Handler],
        *handlers: Handler,
        is_return_delegated: bool = True
    ):
        super().__init__(handler_resource, *handlers)
        self.is_return_delegated = is_return_delegated

    def __call__(self, resource: any) -> any:
        for handler in self.handlers:
            result = handler(resource)

            if self.is_return_delegated and result is not None:
                return result


class ActionChain(HandlerKeeper):
    """Class that implements handling as a chain of actions of handlers."""

    def __call__(self, resource: any) -> any:
        return reduce(
            lambda resource, handler: handler(resource),
            (resource, *self.handlers)
        )


class Brancher:
    """
    Class that implements branching handling of something according to a certain
    condition.

    Delegates the determination of the state of a condition to
    condition_resource_checker.
    """

    def __init__(
        self,
        positive_case_handler: Handler,
        condition_resource_checker: Callable[[any], bool],
        negative_case_resource: Optional[Handler] = None
    ):
        self.positive_case_handler = positive_case_handler
        self.condition_resource_checker = condition_resource_checker
        self.negative_case_resource = negative_case_resource

    @property
    def negative_case_handler(self) -> Handler:
        return (
            self.negative_case_resource
            if self.negative_case_resource is not None
            else lambda _: None
        )

    @negative_case_handler.setter
    def negative_case_handler(self, negative_case_resource: Optional[Handler]) -> None:
        self.negative_case_resource = negative_case_resource

    def __call__(self, resource: any) -> any:
        return (
            self.positive_case_handler
            if self.condition_resource_checker(resource)
            else self.negative_case_handler
        )(resource)