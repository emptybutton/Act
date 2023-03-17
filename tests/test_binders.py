from functools import partial
from typing import Optional, Any, Iterable, Callable

from pytest import mark

from pyhandling.binders import *
from pyhandling.testing import calling_test_from
from pyhandling.tools import ArgumentPack, ArgumentKey
from tests.mocks import Counter


test_binders = calling_test_from(
    (post_partial, 0, [ArgumentPack.of(lambda r: r, 0), ArgumentPack()]),
    (post_partial, 0.1, [ArgumentPack.of(lambda a, b: a / b, 10), ArgumentPack.of(1)]),
    (post_partial, 1.1, [ArgumentPack.of(lambda a, b, *, c: a / b + c, 10, c=1), ArgumentPack.of(1)]),
    (post_partial, 1.1, [ArgumentPack.of(lambda a, b, *, c: a / b + c, 10), ArgumentPack.of(1, c=1)]),
    (post_partial, 12, [ArgumentPack.of(lambda a, b, *, c=10: a / b + c, 2), ArgumentPack.of(4)]),

    (mirror_partial, 4, [ArgumentPack.of(lambda a, b, c: a / b + c, 2, 3, 6), ArgumentPack()]),
    (mirror_partial, 4, [ArgumentPack.of(lambda a, b, c: a / b + c, 2, 3), ArgumentPack.of(6)]),
    (mirror_partial, 4, [ArgumentPack.of(lambda a, b, *, c=0: a / b + c, 3, 6, c=2), ArgumentPack()]),
    (mirror_partial, 4, [ArgumentPack.of(lambda a, b, *, c=0: a / b + c, 3, 6), ArgumentPack.of(c=2)]),
    (mirror_partial, 4, [ArgumentPack.of(lambda a, b, c, *, f=10: a/b + c/f, 20), ArgumentPack.of(8, 4)]),

    (closed, 256, [ArgumentPack.of(lambda a, b: a + b), ArgumentPack.of(250), ArgumentPack.of(6)]),
    (closed, 64, [
        ArgumentPack.of(lambda a, b: a / b, closer=post_partial),
        ArgumentPack.of(2),
        ArgumentPack.of(128)
    ]),

    (eventually, 128, [ArgumentPack.of(lambda a, b: a + b, 100, 28), ArgumentPack.of(1, 2, 3)]),
    (eventually, 128, [ArgumentPack.of(lambda a, b: a + b, 100, 28), ArgumentPack()]),

    (unpackly, 8, [
        ArgumentPack.of(lambda a, b, c: a / b + c),
        ArgumentPack.of(ArgumentPack.of(8, 4, 6))
    ])
)


@mark.parametrize('call_number', tuple(range(4)) + (8, 128, 1024))
def test_returnly_call_number(call_number: int):
    call_counter = Counter()

    returnly_proxy_counter = returnly(call_counter)

    for _ in range(call_number):
        returnly_proxy_counter(2)

    assert call_counter.counted == call_number * 2


@mark.parametrize(
    'input_args, input_kwargs, argument_key_to_return, result',
    [
        ((1, 2, 3), dict(), ArgumentKey(0), 1),
        ((8, 16, 32), dict(), ArgumentKey(1), 16),
        ((64, 128, 256), dict(), ArgumentKey(2), 256),
        ((1, ), dict(b=2, c=3), ArgumentKey(0), 1),
        ((1, 2), dict(c=42), ArgumentKey('c', is_keyword=True), 42),
        ((1, ), dict(b=2, c=3), ArgumentKey('b', is_keyword=True), 2),
        (tuple(), dict(a=2, b=4, c=8), ArgumentKey('a', is_keyword=True), 2),
        ((1, 2, 3), dict(), None, 1),
        ((8, 16), dict(c=32), None, 8),
        ((21, ), dict(b=42, c=84), None, 21)
    ]
)
def test_returnly_by_formula_function(
    input_args: tuple,
    input_kwargs: dict,
    argument_key_to_return: Optional[ArgumentKey],
    result: Any
):
    assert returnly(
        lambda a, b, c: a + b + c,
        **(
            {'argument_key_to_return': argument_key_to_return}
            if argument_key_to_return is not None
            else dict()
        )
    )(*input_args, **input_kwargs) == result