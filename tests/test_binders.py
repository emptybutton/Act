from pyhandling.binders import post_partial, mirror_partial, close, unpackly
from pyhandling.tools import ArgumentPack


def sum_of(first, second, third=3, fourth=4):
    """Stub function for testing currying."""

    return first + second + third + fourth


def test_post_partial():
    assert post_partial(sum_of, 2)(1) == sum_of(1, 2)


def test_mirror_partial():
    assert (
        mirror_partial(sum_of, (2, ), (1, ))(third=tuple(), fourth=tuple())
        == sum_of((1, ), (2, ), tuple(), tuple())
    )


def test_default_closed():
    assert closed(sum_of)(1)(2) == 3


def test_closed_by_post_partial():
    assert closed(sum_of, closer=post_partial)(4)(60) == 64


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


@mark.parametrize(
    'binded_numbers, not_counted_numbers',
    [
        (tuple(range(10)), ) * 2,
        ((1, 2, 3, 6), (200, 100, 123, 54, 13, 42)),
        (tuple(), tuple())
    ]
)
def test_eventually(binded_numbers: Iterable[int | float], not_counted_numbers: Iterable[int | float]):
    assert eventually(lambda *numbers: sum(numbers), *binded_numbers)(
        *not_counted_numbers) == sum(binded_numbers
    )


def test_unpackly_via_argument_pack():
    assert (
        unpackly(sum_of)(ArgumentPack.of(2, 4, third=6, fourth=8))
        == sum_of(2, 4, third=6, fourth=8)
    )