from functools import partial
from operator import add

from act.objects import *
from act.testing import case_of
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
    (lambda: obj(_=1, __call__=lambda v: v + 5)(3), 8),
)


test_obj_with_method = case_of(
    (lambda: obj(value=5, method=as_method(lambda o, v: o.value + v)).method(3), 8)
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


test_like = case_of(
    (lambda: like(4)(4), True),
    (lambda: like(4.)(4), True),
    (lambda: like(8)(4), False),
    (lambda: like(None)(None), True),
    (lambda: like(None)(4), False),
    (lambda: like('a')('a'), True),
    (lambda: like('a')('b'), False),
    (lambda: like([1, 2, 3])([1, 2, 3]), True),
    (lambda: like([1, 2, 3])([1, 2, 3, 4]), False),
    (lambda: like((1, 2, 3))((1, 2, 3, 4)), False),
    (lambda: like([1, 2, 3])((1, 2, 3, 4)), False),
    (lambda: like([1, 2, 3])((1, 2, 3)), False),
    (lambda: like(print)(print), True),
    (lambda: like(print)(pow), False),
    (lambda: like(str)(str), True),
    (lambda: like(str)(bool), False),
    (lambda: like(MockA(1))(MockA(1)), True),
    (lambda: like(MockA(1))(MockA(2)), False),
    (lambda: like(MockA(1))(MockB(2)), False),
    (
        lambda: like(nested(MockA(1), by=MockA, times=2000))(
            nested(MockA(2), by=MockA, times=2000),
        ),
        False,
    ),
    (
        lambda: like(nested(MockA(1), by=MockA, times=2000))(
            nested(MockA(1), by=MockA, times=2000),
        ),
        True,
    ),
)


def test_recursive_like():
    a = MockA(None)
    b = MockA(None)
    c = MockA(None)
    d = MockA(None)

    a.a = c
    b.a = d
    c.a = b
    d.a = a

    assert not like(b)(a)


test_to_attribute = case_of((
    lambda: to_attribute('a', lambda a: a + 5)(MockA(3)).a, 8
))


def test_to_attribute_with_immutability():
    obj_ = MockA(3)

    result = to_attribute('a', lambda a: a + 5)(obj_)

    assert isinstance(result, MockA)
    assert result is not obj_
    assert result.a == 8


def test_to_attribute_with_mutability():
    obj_ = MockA(3)

    result = to_attribute('a', lambda a: a + 5, mutably=True)(obj_)

    assert result is obj_
    assert result.a == 8


test_to_attribute_without_attribute = case_of((
    lambda: to_attribute('b', lambda b: [b])(MockA(3)).b, [None]
))


test_temp_creation = case_of(
    (lambda: temp()().__dict__, dict()),
    (lambda: temp(a=int)(4).__dict__, dict(a=4)),
    (lambda: temp(a=int)(a=4).__dict__, dict(a=4)),
    (lambda: temp(a=int, b=int)(4, 8).__dict__, dict(a=4, b=8)),
    (lambda: temp(a=int, b=int)(a=4, b=8).__dict__, dict(a=4, b=8)),
    (lambda: temp(a=int, b=int)(4, b=8).__dict__, dict(a=4, b=8)),
    (
        lambda: temp(a=int, b=int, c=int, d=int, e=int, f=int)(
            1, 2, 3, 4, 5, 6
        ).__dict__,
        dict(a=1, b=2, c=3, d=4, e=5, f=6),
    ),
    (
        lambda: temp(a=int, b=int, c=int, d=int, e=int, f=int)(
            a=1, b=2, c=3, d=4, e=5, f=6
        ).__dict__,
        dict(a=1, b=2, c=3, d=4, e=5, f=6),
    ),
    (
        lambda: temp(a=int, b=int, c=int, d=int, e=int, f=int)(
            1, 2, 3, d=4, e=5, f=6
        ).__dict__,
        dict(a=1, b=2, c=3, d=4, e=5, f=6),
    ),
)


test_temp_comprasion = case_of(
    (lambda: temp() == temp(), True),
    (lambda: temp(a=str) == temp(a=str), True),
    (lambda: temp(a=str) == temp(a=int), False),
    (lambda: temp(a=str, b=int) == temp(a=int, b=int), False),
    (lambda: temp(a=int, b=int, c=int) == temp(a=int, b=int), False),
    (lambda: temp(a=int, b=int) == temp(a=int, b=int, c=int), False),
    (lambda: temp(a=int, b=int) == temp(), False),
)


test_temp_sum = case_of(
    (lambda: temp(a=int) & temp() == temp(a=int), True),
    (lambda: temp() & temp(b=str) == temp(b=str), True),
    (lambda: temp(a=int) & temp(b=str) == temp(a=int, b=str), True),
    (lambda: temp(a=int) & temp(b=str) == temp(a=int, b=str), True),
    (
        lambda: (
            temp(a=int, b=int) & temp(a=float, c=int)
            == temp(a=float, b=int, c=int)
        ),
        True,
    ),
)


test_temp_with_values = case_of(
    (lambda: (temp() & obj(a=1))().__dict__, dict(a=1)),
    (lambda: (obj(a=1) & temp())().__dict__, dict(a=1)),
    (lambda: temp(a=int) & obj() == temp(a=int), True),
    (lambda: (temp(a=int) & obj(b=2))(1).__dict__, dict(a=1, b=2)),
    (
        lambda: (obj(a=1) & temp(b=int) & obj(c=3) & temp(d=int))(2, 4).__dict__,
        dict(a=1, b=2, c=3, d=4),
    ),
)
