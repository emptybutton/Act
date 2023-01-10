from typing import Optional, Self, Iterable, Callable, Type

from pyhandling.tools import ArgumentPack
from pyhandling.branchers import HandlerKeeper, ReturnFlag, MultipleHandler, ActionChain, mergely, recursively, on_condition, rollbackable, returnly, eventually, then

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


@mark.parametrize(
    "handler, checker, resource, result",
    [
        (lambda x: x + 1, lambda x: x < 10, 0, 10),
        (lambda x: x - 1, lambda x: x > 10, 0, 0),
        (lambda x: x ** x, lambda x: x > 10, 10, 10)
    ]
)
def test_recursively(
    handler: Callable[[any], any],
    checker: Callable[[any], bool],
    resource: any,
    result: any
):
    assert recursively(handler, checker)(resource) == result


@mark.parametrize(
    "number_of_handler_calls, number_of_checker_calls",
    [(i, i + 1) for i in range(3)] + [(100, 101), (653, 654), (999, 1000)]
)
def test_recursively_handler_execution_sequences(
    number_of_handler_calls: int,
    number_of_checker_calls: int
):
    handling_counter = Counter()
    checking_counter = Counter()

    recursively(
        lambda _: handling_counter(),
        lambda _: checking_counter() or checking_counter.counted < number_of_checker_calls
    )(None)

    assert number_of_handler_calls == handling_counter.counted
    assert number_of_checker_calls == checking_counter.counted


@mark.parametrize(
    "max_recursion_depth",
    tuple(range(4)) + (10, 24, 128, 1000, 1256, 10_000, 100_000)
)
def test_recursively_depth_exceedance(max_recursion_depth: int):
    handling_counter = Counter()

    with raises(HandlingRecursionDepthError):
        recursively(
            lambda _: handling_counter(),
            lambda _: True,
            max_recursion_depth=max_recursion_depth
        )(None)

    assert handling_counter.counted == max_recursion_depth


@mark.parametrize(
    "input_number, result",
    [
        (0, 1),
        (3, 27),
        (10, 10 ** 10),
        (20, 400),
        (100, 10_000)
    ]
)
def test_on_condition_by_numeric_functions(
    input_number: int | float,
    result: any
):
    assert on_condition(
        lambda x: x <= 10,
        lambda x: x ** x,
        else_=lambda x: x * x
    )(input_number) == result


@mark.parametrize(
    "func, input_args, input_kwargs, result",
    [
        (lambda x: 1 / x, (1, ), dict(), 1),
        (lambda x: 1 / x, (2, ), dict(), 0.5),
        (lambda x, y: x + y, (1, 2), dict(), 3),
        (lambda x, y, z: x + y + z, (1, 2), {'z': 3}, 6),
        (lambda x, y, z: x + y + z, (2, ), {'y': 4, 'z': 6}, 12),
        (lambda x, y: x + y, tuple(), {'x': 4, 'y': 6}, 10),
        (lambda: 42, tuple(), dict(), 42),
    ]
)
def test_rollbackable_without_error(
    func: Callable,
    input_args: Iterable, 
    input_kwargs: dict,
    result: any
):
    assert rollbackable(
        func,
        lambda error: fail(
            f"Catching the unexpected error {error.__class__.__name__} \"{str(error)}\""
        )
    )(*input_args, **input_kwargs) == result


@mark.parametrize(
    "func, input_args, error_type",
    [
        (lambda x: x / 0, (42, ), ZeroDivisionError),
        (lambda x, y: x + y, (1, '2'), TypeError),
        (lambda mapping, key: mapping[key], (tuple(), 0), IndexError),
        (lambda mapping, key: mapping[key], (tuple(), 10), IndexError),
        (lambda mapping, key: mapping[key], ((1, 2), 2), IndexError),
        (lambda mapping, key: mapping[key], (dict(), 'a'), KeyError),
        (lambda mapping, key: mapping[key], ({'a': 42}, 'b'), KeyError),
        (lambda: int('1' + '0'*4300), tuple(), ValueError)
    ]
)
def test_rollbackable_with_error(
    func: Callable,
    input_args: Iterable,
    error_type: Type[Exception]
):
    assert type(rollbackable(func, lambda error: error)(*input_args)) is error_type


