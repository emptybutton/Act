from inspect import signature
from typing import Optional, Any

from pytest import mark

from pyhandling.arguments import ArgumentPack, ArgumentKey
from pyhandling.partials import *
from pyhandling.testing import calling_test_case_of
from tests.mocks import Counter


test_post_partial = calling_test_case_of(
    (lambda: post_partial(lambda r: r, 0)(), 0),
    (lambda: post_partial(lambda a, b: a / b, 10)(1), 0.1),
    (lambda: post_partial(lambda a, b, *, c: a / b + c, 10, c=1)(1), 1.1),
    (lambda: post_partial(lambda a, b, *, c: a / b + c, 10)(1, c=1), 1.1),
    (lambda: post_partial(lambda a, b, *, c=10: a / b + c, 2)(4), 12),
    (
        lambda: post_partial(lambda a, *args, **kwargs: (a, *args, kwargs), 2, c=3)(1),
        (1, 2, dict(c=3))
    ),
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
