from typing import Optional, Self, Iterable, Callable

from pyhandling.branchers import HandlerKeeper, ReturnFlag, MultipleHandler, ActionChain, mergely, recursively
from pyhandling.tools import ArgumentPack

from pytest import mark


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
def test_neutral_action_chain_calling(args: Iterable, kwargs: dict):
    assert ActionChain()(*args, **kwargs) == ArgumentPack(args, kwargs)


@mark.parametrize(
    "handlers, input_resource, result",
    [
        [(lambda x: x + 2, lambda x: x ** x), 2, 256],
        [(MockHandler(), ), 1, 1],
        [(MockHandler(), ), str(), str()],
        [(lambda x: None, ), 256, None],
    ]
)
def test_action_chain_calling(handlers: Iterable[Callable[[any], any]], input_resource: any, result: any):
    assert ActionChain(handlers)(input_resource) == result


@mark.parametrize(
    'first_nodes, second_nodes',
    [
        [(MockHandler(), lambda x: x + 1), (MockHandler(), )],
        [(MockHandler(), lambda x: x + 1), tuple()],
        [tuple(), (MockHandler(), )],
        [tuple(), tuple()]
    ]
)
def test_action_chain_connection_to_other(first_nodes: Iterable[Callable], second_nodes: Iterable[Callable]):
    assert (
        ActionChain(*first_nodes, *second_nodes).handlers
        == ActionChain(first_nodes).clone_with(ActionChain(second_nodes)).handlers
        == (
            ActionChain(second_nodes).clone_with(
                ActionChain(first_nodes), is_other_handlers_on_the_left=True
            ).handlers
        )
    )


@mark.parametrize(
    'first_nodes, second_nodes',
    [
        [(MockHandler(), lambda x: x + 1), (MockHandler(), MockHandler())],
        [(MockHandler(), lambda x: x + 1, MockHandler()), (MockHandler(), )],
        [(MockHandler(), ), (MockHandler(), MockHandler())],
        [(MockHandler(), lambda x: x + 1), tuple()],
        [tuple(), (MockHandler(), )],
        [tuple(), tuple()]
    ]
)
def test_action_chain_connection_to_raw_handlers(first_nodes: Iterable[Callable], second_nodes: Iterable[Callable]):
    assert (
        ActionChain(*first_nodes, *second_nodes).handlers
        == ActionChain(first_nodes).clone_with(*second_nodes).handlers
        == (
            ActionChain(second_nodes).clone_with(
                *first_nodes, is_other_handlers_on_the_left=True
            ).handlers
        )
    )


@mark.parametrize(
    'handlers, connetction_handler',
    [
        [(MockHandler(), lambda x: x + 1), MockHandler()],
        [(MockHandler(), lambda x: x + 1, MockHandler()), lambda x: x**2],
        [(MockHandler(), ), lambda x: x + 1],
        [tuple(), MockHandler()],
    ]
)
def test_action_chain_connection_through_operators(handlers: Iterable[Callable[[any], any]], connetction_handler: Callable[[any], any]):
    assert (
        ActionChain(*(*handlers, connetction_handler)).handlers
        == (ActionChain(*handlers) | connetction_handler).handlers
        == (ActionChain(*handlers) >> connetction_handler).handlers
    )


@mark.parametrize(
    "original_branchers, intermediate_brancher, is_on_input, is_on_output, input_resource, result",
    [
        [(lambda x: x + 2, lambda x: x * x), lambda x: x * 2, False, False, 2, 64],
        [(lambda x: x + 2, lambda x: x + 10, lambda x: x * 2), lambda x: x + 1, False, False, 2, 32],
        [(MockHandler(), lambda x: x - 1), lambda x: x ** x, True, False, 2, 255],
        [(MockHandler(), lambda x: x * 2), lambda x: x * x, False, True, 2, 64],
        [(MockHandler(), MockHandler(), MockHandler()), lambda x: x + 1, True, True, 0, 4],
        [tuple(), lambda x: x + 1, False, False, 128, ArgumentPack.create_via_call(128)],
        [tuple(), lambda x: x * x, True, False, 8, 64],
        [tuple(), lambda x: x * x, False, True, 8, 64],
        [tuple(), lambda x: x * x, True, True, 4, 256]
    ]
)
def test_action_chain_cloning_with_intermediate(
    original_branchers: Iterable[Callable[[any], any]],
    intermediate_brancher: Callable[[any], any],
    is_on_input: bool,
    is_on_output: bool,
    input_resource: any,
    result: any
):
    assert ActionChain(original_branchers).clone_with_intermediate(
        intermediate_brancher,
        is_on_input=is_on_input,
        is_on_output=is_on_output
    )(input_resource) == result


@mark.parametrize(
    'input_handlers, output_straightening_handlers',
    [
        [tuple(), tuple()],
        [(ActionChain(), ), tuple()],
        [(MockHandler(1), )] * 2,
        [(MockHandler(1), MockHandler(2))] * 2,
        [(MockHandler(1), MockHandler(2), MockHandler(3))] * 2,
        [
            (ActionChain(MockHandler(1), MockHandler(2)), ),
            (MockHandler(1), MockHandler(2))
        ],
        [
            (ActionChain(MockHandler(1), MockHandler(2)), MockHandler(3)),
            (MockHandler(1), MockHandler(2), MockHandler(3))
        ],
        [
            (ActionChain(ActionChain((MockHandler(1), )), MockHandler(2)), MockHandler(3)),
            (MockHandler(1), MockHandler(2), MockHandler(3))
        ],
        [
            (ActionChain(ActionChain(ActionChain([MockHandler(1)]))), ),
            (MockHandler(1), )
        ],
        [ActionChain((ActionChain, ) * 10)((MockHandler(1), )), (MockHandler(1), )]
    ]
)
def test_straightening_action_chains(
    input_handlers: tuple[MockHandler | ActionChain],
    output_straightening_handlers: tuple[MockHandler | ActionChain]
):
    assert ActionChain(input_handlers).handlers == output_straightening_handlers


@mark.parametrize(
    "factor, original_x, original_y, original_z",
    [
        (1, 2, 4, 4), (0.5, 4, 4, 12), (2, 8, 1, -78), (10, 12, 3, 12),
        (0, 1000, 2000, 3000), (100, 10, 10, 0), (-3, 2, -3, 14), (-1, -2, -3, -4)
    ]
)
def test_mergely_by_formula_function(
    factor: int | float,
    original_x: int | float,
    original_y: int | float,
    original_z: int | float,
):
    assert mergely(
        lambda factor: (lambda x, y, z: factor * (x ** y + z)),
        lambda factor: factor * original_x,
        lambda factor: factor * original_y,
        lambda factor: factor * original_z,
    )(factor) == factor * ((factor * original_x) ** (factor * original_y) + (factor * original_z))


