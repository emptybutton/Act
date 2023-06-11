from functools import partial
from operator import not_, add
from typing import Any, Iterable, Container, Literal, Iterator

from pytest import raises, mark

from pyhandling.errors import InvalidInitializationError, UniaError
from pyhandling.objects import *
from pyhandling.testing import case_of
from tests.mocks import MockAction, CustomContext


test_dict_of = case_of(
    (lambda: dict_of(dict(v=8)), dict(v=8)),
    (lambda: dict_of(print), dict()),
    (lambda: dict_of(MockAction(4)), dict(equality_id=4)),
)


test_unia_creation_with_annotations = case_of(
    (lambda: Unia(int), int),
    (lambda: type(Unia(int, float)), Unia),
    (lambda: Unia[int], Unia(int)),
    (lambda: Unia[int, float], Unia(int, float)),
)


def test_unia_creation_without_annotations():
    with raises(UniaError):
        Unia()


@mark.parametrize(
    "value, unia, is_correct",
    (
        (list(), Unia[Iterable], True),
        (list(), Unia[Iterable, Container], True),
        (list(), Unia[Iterable, Container, int], False),
    ),
)
def test_unia(value: Any, unia: Unia, is_correct: bool):
    mode = (lambda r: r) if is_correct else not_

    assert mode(isinstance(value, unia))


test_obj_creation = case_of(
    (lambda: obj().__dict__, dict()),
    (lambda: obj(a=1, b=2).__dict__, dict(a=1, b=2)),
    (lambda: obj(a=1, b=2), obj(a=1, b=2)),
    (lambda: obj(a=1, b=2), obj(b=2, a=1)),
)


test_obj_sum = case_of(
    (
        lambda: obj.of(MockAction(0), CustomContext(1)),
        obj(equality_id=0, enter_result=1),
    ),
    (lambda: obj(a=1) & obj(), obj(a=1)),
    (lambda: obj(a=1) & obj(b=2), obj(a=1, b=2)),
    (lambda: obj(a=1) & obj(a=2), obj(a=2)),
    (lambda: obj(some=8) & MockAction(4), obj(some=8, equality_id=4)),
    (lambda: MockAction(4) & obj(some=8), obj(some=8, equality_id=4)),
)


test_callable_obj = case_of(
    (lambda: callable(obj(a=1, b=2)), False),
    (lambda: callable(obj(a=1, __call__=lambda _: ...)), True),
    (lambda: obj(action=partial(add, 10)).action(6), 16),
    (lambda: obj(some=5, __call__=lambda o: o.some + 3)(), 8),
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
            CustomContext("result"),
            MockAction('id'),
        )),
        (MockAction, dict(enter_result="result", equality_id='id')),
    ),
)
