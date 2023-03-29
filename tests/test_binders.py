from inspect import signature
from typing import Optional, Any

from pytest import mark

from pyhandling.binders import *
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import ArgumentPack, ArgumentKey
from tests.mocks import Counter


test_post_partial = calling_test_case_of(
    (lambda: post_partial(lambda r: r, 0)(), 0),
    (lambda: post_partial(lambda a, b: a / b, 10)(1), 0.1),
    (lambda: post_partial(lambda a, b, *, c: a / b + c, 10, c=1)(1), 1.1),
    (lambda: post_partial(lambda a, b, *, c: a / b + c, 10)(1, c=1), 1.1),
    (lambda: post_partial(lambda a, b, *, c=10: a / b + c, 2)(4), 12),
)


test_mirror_partial = calling_test_case_of(
    (lambda: mirror_partial(lambda a, b, c: a / b + c, 2, 3, 6)(), 4),
    (lambda: mirror_partial(lambda a, b, c: a / b + c, 2, 3)(6), 4),
    (lambda: mirror_partial(lambda a, b, *, c=0: a / b + c, 3, 6, c=2)(), 4),
    (lambda: mirror_partial(lambda a, b, *, c=0: a / b + c, 3, 6)(c=2), 4),
    (lambda: mirror_partial(lambda a, b, c, *, f=10: a/b + c/f, 20)(8, 4), 4),
)


test_closed = calling_test_case_of(
    (lambda: closed(lambda a, b: a + b)(250)(6), 256),
    (lambda: closed(lambda a, b: a / b, close=post_partial)(2)(128), 64),
)


test_eventually = calling_test_case_of(
    (lambda: eventually(lambda a, b: a + b, 100, 28)(1, 2, 3), 128),
    (lambda: eventually(lambda a, b: a + b, 100, 28)(), 128),
)


test_unpackly = calling_test_case_of(
    (lambda: unpackly(lambda a, b, c: a / b + c)(ArgumentPack.of(8, 4, 6)), 8),
)


test_fragmentarily = calling_test_case_of(
    (lambda: fragmentarily(lambda a, b, c: a / b + c)(10, 2, 3), 8),
    (lambda: fragmentarily(lambda a, b, c: a / b + c)(10, 2)(3), 8),
    (lambda: fragmentarily(lambda a, b, c: a / b + c)(10)(2, 3), 8),
    (lambda: fragmentarily(lambda a, b, c: a / b + c)(10)(2)(3), 8),
    (lambda: signature(fragmentarily(lambda a, b, c: ...)('a')), signature(lambda b, c: ...)),
    (lambda: fragmentarily(lambda: 16)(), 16),
    (lambda: fragmentarily(lambda *_: 16)(), 16),
    (lambda: fragmentarily(lambda *_, a=...: 16)(), 16),
    (lambda: fragmentarily(lambda *_, **__: 16)(), 16),
    (lambda: fragmentarily(lambda a, k=0: a + k)(k=4)(60), 64),
    (
        lambda: (
            fragmentarily(
                lambda *numbers, **kw_nubers: sum((*numbers, *kw_nubers.values()))
            )(1, 2, 5, a=5, b=3)
        ),
        16,
    )
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