from typing import Optional, Self, Iterable, Callable

from pyhandling.branchers import HandlerKeeper, ReturnFlag, MultipleHandler, ActionChain
from pyhandling.tools import ArgumentPack

from pytest import mark


class MockHandler:
    def __repr__(self) -> str:
        return "<MockHandler>"

    def __call__(self, resource: any) -> any:
        return resource


@mark.parametrize(
    'first_handler_resource, handlers',
    [
        [MockHandler(), (MockHandler(), MockHandler(), MockHandler())],
        [(MockHandler(), MockHandler()), (MockHandler(), MockHandler())]
    ]
)
def test_handler_keeper(
    first_handler_resource: Iterable[Callable[[any], any]] | Callable[[any], any],
    handlers: Callable[[any], any]
):
    assert (
        set(HandlerKeeper(first_handler_resource, *handlers).handlers)
        == set(handlers) | set(
            first_handler_resource
            if isinstance(first_handler_resource, Iterable)
            else (first_handler_resource, )
        )
    )


@mark.parametrize(
    'handlers, return_flag, resource, result',
    [
        [(MockHandler(), MockHandler(), MockHandler()), ReturnFlag.first_received, 1, 1],
        [(MockHandler(), MockHandler(), MockHandler()), ReturnFlag.first_received, 100, 100],
        [(MockHandler(), lambda number: number**2), ReturnFlag.last_thing, 16, 256],
        [
            (MockHandler(), lambda number: number + 2, lambda number: number * 2),
            ReturnFlag.everything,
            8,
            (8, 10, 16)
        ],
        [(MockHandler(), ), ReturnFlag.nothing, 1, None]
    ]
)
def test_multiple_handler_handling(
    handlers: Iterable[Callable[[any], any]],
    return_flag: ReturnFlag,
    resource: any,
    result: any
):
    assert MultipleHandler(*handlers, return_flag=return_flag)(resource) == result


@mark.parametrize(
    'args, kwargs',
    [
        [(1, 2, 3), {'a': 1, 'b': 2}],
        [(1, 2, 3), dict()],
        [tuple(), {'a': 1, 'b': 2}],
        [tuple(), dict()]
    ]
)
def test_neutral_action_chain_output(args: Iterable, kwargs: dict):
    assert ActionChain()(*args, **kwargs) == ArgumentPack(args, kwargs)


@mark.parametrize(
    'first_nodes, second_nodes',
    [
        [(MockHandler(), lambda x: x + 1), (MockHandler(), )],
        [(MockHandler(), lambda x: x + 1), tuple()],
        [tuple(), (MockHandler(), )],
        [tuple(), tuple()]
    ]
)
def test_action_chain_connections(first_nodes: Iterable[Callable], second_nodes: Iterable[Callable]):
    assert (
        ActionChain(*first_nodes, *second_nodes).handlers
        == ActionChain(first_nodes).clone_with(ActionChain(second_nodes)).handlers
        == (ActionChain(first_nodes) | ActionChain(second_nodes)).handlers
        == (ActionChain(first_nodes) >> ActionChain(second_nodes)).handlers
    )