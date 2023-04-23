from typing import Iterable, Callable, Any

from pytest import mark

from pyhandling.arguments import *
from pyhandling.testing import calling_test_case_of


@mark.parametrize(
    'args, kwargs',
    [
        ((1, 2, 3), dict(a=4, b=5, c=6)),
        ((1, ), dict(a=4, b=5, c=6)),
        (tuple(), dict(a=4, b=5, c=6)),
        ((1, 2, 3), dict()),
        (tuple(), dict()),
    ]
)
def test_argument_pack_creation_via_call(args: Iterable, kwargs: dict):
    assert ArgumentPack.of(*args, **kwargs) == ArgumentPack(args, kwargs)


@mark.parametrize(
    'first_args, first_kwargs, second_args, second_kwargs',
    [
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), tuple(), dict(d=7, e=8, f=9)),
        ((1, 2, 3), dict(), (4, 5, 6), dict()),
        (tuple(), dict(), ) * 2,
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(a=7, b=8, c=9)),
    ]
)
def test_argument_pack_merger(
    first_args: Iterable,
    first_kwargs: dict,
    second_args: Iterable,
    second_kwargs: dict,
):
    assert (
        ArgumentPack(first_args, first_kwargs).merge_with(
            ArgumentPack(second_args, second_kwargs),
        )
        == ArgumentPack.of(
            *first_args,
            *second_args,
            **(first_kwargs | second_kwargs),
        )
    )


@mark.parametrize(
    'first_args, first_kwargs, second_args, second_kwargs',
    [
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), (4, 5, 6), dict(d=7, e=8, f=9)),
        (tuple(), dict(a=4, b=5, c=6), tuple(), dict(d=7, e=8, f=9)),
        ((1, 2, 3), dict(), (4, 5, 6), dict()),
        (tuple(), dict(), ) * 2,
        ((1, 2, 3), dict(a=4, b=5, c=6), (4, 5, 6), dict(a=7, b=8, c=9)),
    ]
)
def test_argument_pack_expanding(
    first_args: Iterable,
    first_kwargs: dict,
    second_args: Iterable,
    second_kwargs: dict
):
    assert (
        ArgumentPack(first_args, first_kwargs).expand_with(
            *second_args,
            **second_kwargs
        )
        == ArgumentPack.of(
            *first_args,
            *second_args,
            **(first_kwargs | second_kwargs),
        )
    )


@mark.parametrize(
    'func, argument_pack, result',
    [
        (lambda a, b, c: a * b * c, ArgumentPack((1, 2, 3)), 6),
        (lambda a, b, c: a + b + c, ArgumentPack((8, 4), dict(c=30)), 42),
        (
            lambda a, b, c: a ** b ** c,
            ArgumentPack(kwargs=dict(a=2, b=2, c=3)),
            256,
        ),
        (lambda: 48, ArgumentPack(), 48),
    ]
)
def test_argument_pack_calling(
    func: Callable,
    argument_pack: ArgumentPack,
    result: Any,
):
    assert argument_pack.call(func) == result


@mark.parametrize(
    'argument_pack, argument_key, result',
    [
        (ArgumentPack((1, 2, 3)), ArgumentKey(0), 1),
        (ArgumentPack((2, 8, 32, 64, 128), dict(a=1)), ArgumentKey(3), 64),
        (
            ArgumentPack((4, 2), dict(a=32, b=64, c=128)),
            ArgumentKey('c', is_keyword=True),
            128,
        ),
        (
            ArgumentPack(kwargs=dict(a=1, b=5, c=7)),
            ArgumentKey('b', is_keyword=True),
            5
        ),
    ]
)
def test_argument_pack_getting_argument_by_key(
    argument_pack: ArgumentPack,
    argument_key: ArgumentKey,
    result: Any
):
    assert argument_pack[argument_key] == result


@mark.parametrize(
    'args, kwargs, result_argument_pack',
    [
        ((1, 2, 3), dict(), ArgumentPack((1, 2, 3))),
        (
            (8, 32, 64),
            dict(a=1, b=2, c=3),
            ArgumentPack((8, 32, 64), dict(a=1, b=2, c=3)),
        ),
        (
            tuple(),
            dict(x=16, y=4, z=1),
            ArgumentPack(kwargs=dict(x=16, y=4, z=1)),
        ),
        (tuple(), dict(), ArgumentPack()),
        ((42, ), dict(x=16), ArgumentPack((42, ), dict(x=16))),
        ((42, ), dict(), ArgumentPack((42, ))),
        ((ArgumentPack((42, )), ), dict(), ArgumentPack((42, ))),
        (
            (ArgumentPack((42, ), dict(a=32)), ),
            dict(),
            ArgumentPack((42, ), dict(a=32)),
        ),
    ]
)
def test_as_argument_pack(
    args: Iterable,
    kwargs: dict,
    result_argument_pack: ArgumentPack,
):
    assert as_argument_pack(*args, **kwargs) == result_argument_pack


test_unpackly = calling_test_case_of(
    (lambda: unpackly(lambda a, b, c: a / b + c)(ArgumentPack.of(8, 4, 6)), 8),
)
