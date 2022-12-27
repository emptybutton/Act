from typing import NewType, Callable, Iterable, Self, Optional


Handler = NewType('Handler', Callable[[any], any])


class HandlerKeeper:
    def __init__(self, handler_resource: Handler | Iterable[Handler], *handlers: Handler):
        self.handlers = (
            tuple(handler_resource)
            if isinstance(handler_resource, Iterable)
            else (handler_resource, )
        ) + handlers
