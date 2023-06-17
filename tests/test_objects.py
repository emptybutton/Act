from functools import partial
from operator import add

from pyhandling.objects import *
from pyhandling.testing import case_of
from tests.mocks import MockA, MockB, nested


test_dict_of = case_of(
    (lambda: dict_of(dict(v=8)), dict(v=8)),
    (lambda: dict_of(print), dict()),
    (lambda: dict_of(MockA(4)), dict(a=4)),
)


test_obj_creation = case_of(
    (lambda: obj().__dict__, dict()),
    (lambda: obj(a=1, b=2).__dict__, dict(a=1, b=2)),
    (lambda: obj(a=1, b=2), obj(a=1, b=2)),
    (lambda: obj(a=1, b=2), obj(b=2, a=1)),
)


test_obj_reconstruction = case_of(
    (lambda: obj(a=1) + 'b', obj(a=1, b=None)),
    (lambda: obj(a=1) + 'a', obj(a=1)),
    (lambda: obj() + 'a', obj(a=None)),
    (lambda: obj(a=1, b=2) - 'a', obj(b=2)),
    (lambda: obj(b=2) - 'a', obj(b=2)),
    (lambda: obj(b=2) - 'b', obj()),
    (lambda: obj() - 'b', obj()),
)


test_obj_sum = case_of(
    (
        lambda: obj.of(MockA(1), MockB(2)),
        obj(a=1, b=2),
    ),
    (lambda: obj(a=1) & obj(), obj(a=1)),
    (lambda: obj(a=1) & obj(b=2), obj(a=1, b=2)),
    (lambda: obj(a=1) & obj(a=2), obj(a=2)),
    (lambda: obj(a=1) & MockB(2), obj(a=1, b=2)),
    (lambda: MockA(1) & obj(b=2), obj(a=1, b=2)),
)


test_callable_obj = case_of(
    (lambda: callable(obj(a=1, b=2)), False),
    (lambda: callable(obj(a=1, __call__=lambda _: ...)), True),
    (lambda: obj(action=partial(add, 10)).action(6), 16),
    (lambda: obj(some=5, __call__=lambda o: o.some + 3)(), 8),
    (lambda: obj(some=2, __call__=lambda o, v: o.some + 3 + v)(3), 8),
)


test_obj_with_method = case_of(
    (lambda: obj(value=5, method=method_of(lambda o, v: o.value + v)).method(3), 8)
)


test_void = case_of(
    (lambda: void & obj(a=1), obj(a=1)),
    (lambda: void & void, void),
)


test_of = case_of(
    (lambda: of(obj(a=1, b=2), obj(c=3)), obj(a=1, b=2, c=3)),
    (lambda: of(obj(a=2), obj(a=1)), obj(a=2)),
    (
        lambda: (lambda r: (type(r), r.__dict__))(of(
            MockB(2),
            MockA(1),
        )),
        (MockA, dict(a=1, b=2)),
    ),
)
