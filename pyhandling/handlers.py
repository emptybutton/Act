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
