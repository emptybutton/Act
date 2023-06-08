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
def test_arguments_creation_via_call(args: Iterable, kwargs: dict):
    assert Arguments.of(*args, **kwargs) == Arguments(args, kwargs)


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
def test_argument_pack_merging(
    first_args: Iterable,
    first_kwargs: dict,
    second_args: Iterable,
    second_kwargs: dict,
):
    assert (
        Arguments(first_args, first_kwargs).expanded_with(
            Arguments(second_args, second_kwargs),
        )
        == Arguments.of(
            *first_args,
            *second_args,
            **(first_kwargs | second_kwargs),
        )
    )


@mark.parametrize(
    'func, argument_pack, result',
    [
        (lambda a, b, c: a * b * c, Arguments((1, 2, 3)), 6),
        (lambda a, b, c: a + b + c, Arguments((8, 4), dict(c=30)), 42),
        (
            lambda a, b, c: a ** b ** c,
            Arguments(kwargs=dict(a=2, b=2, c=3)),
            256,
        ),
        (lambda: 48, Arguments(), 48),
    ]
)
def test_argument_pack_calling(
    func: Callable,
    argument_pack: Arguments,
    result: Any,
):
    assert argument_pack.call(func) == result


@mark.parametrize(
    'argument_pack, argument_key, result',
    [
        (Arguments((1, 2, 3)), ArgumentKey(0), 1),
        (Arguments((2, 8, 32, 64, 128), dict(a=1)), ArgumentKey(3), 64),
        (
            Arguments((4, 2), dict(a=32, b=64, c=128)),
            ArgumentKey('c', is_keyword=True),
            128,
        ),
        (
            Arguments(kwargs=dict(a=1, b=5, c=7)),
            ArgumentKey('b', is_keyword=True),
            5
        ),
    ]
)
def test_argument_pack_getting_argument_by_key(
    argument_pack: Arguments,
    argument_key: ArgumentKey,
    result: Any
):
    assert argument_pack[argument_key] == result


test_argument_pack_only_with = calling_test_case_of(
    (
        lambda: Arguments((1, 2, 3), dict(a=4)).only_with(ArgumentKey(0)),
        Arguments((1, )),
    ),
    (
        lambda: Arguments((0, 1, 2, 3), dict(a=4, b=5)).only_with(
            ArgumentKey(0),
            ArgumentKey(2),
            ArgumentKey('a', is_keyword=True)
        ),
        Arguments((0, 2), dict(a=4)),
    ),
)


@mark.parametrize(
    'args, kwargs, result_argument_pack',
    [
        ((1, 2, 3), dict(), Arguments((1, 2, 3))),
        (
            (8, 32, 64),
            dict(a=1, b=2, c=3),
            Arguments((8, 32, 64), dict(a=1, b=2, c=3)),
        ),
        (
            tuple(),
            dict(x=16, y=4, z=1),
            Arguments(kwargs=dict(x=16, y=4, z=1)),
        ),
        (tuple(), dict(), Arguments()),
        ((42, ), dict(x=16), Arguments((42, ), dict(x=16))),
        ((42, ), dict(), Arguments((42, ))),
        ((Arguments((42, )), ), dict(), Arguments((42, ))),
        (
            (Arguments((42, ), dict(a=32)), ),
            dict(),
            Arguments((42, ), dict(a=32)),
        ),
    ]
)
def test_as_arguments(
    args: Iterable,
    kwargs: dict,
    result_argument_pack: Arguments,
):
    assert as_arguments(*args, **kwargs) == result_argument_pack


test_unpackly = calling_test_case_of(
    (lambda: unpackly(lambda a, b, c: a / b + c)(Arguments.of(8, 4, 6)), 8),
    (lambda: unpackly(lambda a, b, c: a / b + c)([8, 4, 6]), 8),
)
