from functools import partial
from operator import add, attrgetter

from pytest import mark, raises

from act.aggregates import Access
from act.objects import *
from act.synonyms import with_
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
    (lambda: obj(a=1) & obj(b=2), obj(b=2, a=1)),
    (lambda: obj(a=1) & obj(a=2), obj(a=2)),
    (lambda: obj(a=1) & MockB(2), obj(a=1, b=2)),
    (lambda: MockA(1) & obj(b=2), obj(a=1, b=2)),
)


test_obj_single_annotating = case_of(
    (lambda: isinstance(MockA(4), obj(a=4)), True),
    (lambda: isinstance(MockA(8), obj(a=4)), False),
    (lambda: isinstance(obj(a=4), obj(a=4)), True),
    (lambda: isinstance(obj(a=4), obj()), True),
    (lambda: isinstance(obj(), obj()), True),
    (lambda: isinstance(obj(a=4, b=2), obj(a=4)), True),
    (lambda: isinstance(obj(a=4, b=2), obj(a=4, b=4)), False),
    (lambda: isinstance(obj(a=4, b=2), obj(a=4, b=2)), True),
    (lambda: isinstance(MockB(4), obj(a=4)), False),
    (lambda: isinstance(MockA(4), obj()), True),
    (lambda: isinstance(MockB(4), obj()), True),
    (lambda: isinstance(obj(a=1, b=2, c=3), obj()), True),
    (lambda: isinstance(obj(), obj()), True),
)


test_obj_union_annotating_with_one_attribute = case_of(
    (lambda: isinstance(MockA(1), obj(a=1) | obj(a=2)), True),
    (lambda: isinstance(MockA(2), obj(a=1) | obj(a=2)), True),
    (lambda: isinstance(MockA(3), obj(a=1) | obj(a=2)), False),
    (lambda: isinstance(MockB(3), obj(a=1) | obj(a=2)), False),
    (lambda: isinstance(obj(a=1), obj(a=1) | obj(a=2)), True),
    (lambda: isinstance(obj(a=2), obj(a=1) | obj(a=2)), True),
    (lambda: isinstance(obj(a=3), obj(a=1) | obj(a=2)), False),
    (lambda: isinstance(obj(b=3), obj(a=1) | obj(a=2)), False),
    (lambda: isinstance(obj(a=1, b=3), obj(a=1) | obj(a=2)), True),
)


test_obj_union_annotating_with_multiple_attributes = case_of(
    (lambda: isinstance(obj(a=1, b=3), obj(a=1) | obj(b=2)), True),
    (lambda: isinstance(obj(a=0, b=2), obj(a=1) | obj(b=2)), True),
    (lambda: isinstance(obj(a=0, b=0, c=0), obj(a=1) | obj(b=2)), False),
    (
        lambda: isinstance(
            obj(a=0, b=0, c=0),
            obj(a=1) | obj(b=2, c=2) | obj(b=3, c=3),
        ),
        False,
    ),
    (
        lambda: isinstance(
            obj(a=0, b=2, c=2),
            obj(a=1) | obj(b=2, c=2) | obj(b=3, c=3),
        ),
        True,
    ),
    (
        lambda: isinstance(
            obj(a=1, b=2, c=3, d=40),
            obj(a=1) | obj(b=2, c=2) | obj(b=3, c=3),
        ),
        True,
    ),
    (
        lambda: isinstance(
            obj(a=0, b=3, c=3, d=40),
            obj(a=1) | obj(b=2, c=2) | obj(b=3, c=3),
        ),
        True,
    ),
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


test_obj_with_descriptor_getting = case_of(
    (lambda: obj(a=5, b=as_descriptor(property(lambda o: o.a + 3))).b, 8),
    (lambda: obj(a=5, b=as_descriptor(lambda o, v: o.a + v)).b(3), 8),
)


def test_obj_with_descriptor_setting():
    object_ = obj(
        a=14,
        b=as_descriptor(property(
            lambda o: o.a + 2,
            lambda o, v: setattr(o, 'a', v * 2),
        )),
    )

    assert object_.b == 16

    object_.b = 3

    assert object_.b == 8


def test_obj_with_only_descriptor_setting():
    object_ = obj(
        a=...,
        b=as_descriptor(property(fset=lambda o, v: setattr(o, 'a', v + 10))),
    )

    object_.b = 6

    assert object_.a == 16


def test_obj_with_only_descriptor_deleting():
    logs = list()

    object_ = obj(
        a=5,
        b=as_descriptor(property(
            fdel=lambda o: logs.append(o.a + 3),
        )),
    )

    del object_.b

    assert not hasattr(object_, 'b')
    assert 'b' in object_.__dict__.keys()

    assert logs == [8]


test_void = case_of(
    (lambda: void & obj(a=1), obj(a=1)),
    (lambda: void & void, void),
)


test_from_ = case_of(
    (lambda: from_(obj(a=1, b=2), obj(c=3)), obj(a=1, b=2, c=3)),
    (lambda: from_(obj(a=2), obj(a=1)), obj(a=2)),
    (
        lambda: (lambda r: (type(r), r.__dict__))(from_(
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
    (lambda: type(temp()), obj),
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
    (lambda: temp(b=str) & temp(a=int) == temp(a=int, b=str), True),
    (
        lambda: (
            temp(a=int, b=int) & temp(a=float, c=int)
            == temp(a=float, b=int, c=int)
        ),
        True,
    ),
)


test_temp_with_values = case_of(
    (lambda: type(temp() & obj(a=1)), obj),
    (lambda: type(obj(a=1) & temp()), obj),
    (lambda: obj(a=1) & temp(), obj(a=1)),
    (lambda: temp() & obj(a=1), obj(a=1)),
    (lambda: temp(a=int) & obj() == temp(a=int), True),
    (lambda: obj() & temp(a=int) == temp(a=int), True),
    (lambda: (temp(a=int) & obj(b=2))(1), obj(a=1, b=2)),
    (
        lambda: (obj(a=1) & temp(b=int) & obj(c=3) & temp(d=int))(2, 4),
        obj(a=1, b=2, c=3, d=4),
    ),
)


test_temp_single_annotating = case_of(
    (lambda: isinstance(MockA(1), temp(a=int)), True),
    (lambda: isinstance(MockB(1), temp(a=int)), False),
    (lambda: isinstance(obj(a=1, b=2), temp(a=int, b=int)), True),
    (lambda: isinstance(obj(b=2, a=1), temp(a=int, b=int)), True),
    (lambda: isinstance(obj(c=3, b=2, a=1), temp(a=int, b=int)), True),
    (lambda: isinstance(obj(c=3, b=2, a=1), temp()), True),
    (lambda: isinstance(obj(), temp()), True),
    (lambda: isinstance(obj(a=1), temp()), True),
)


test_temp_single_annotating_with_values = case_of(
    (lambda: isinstance(obj(a=10, b=2), temp(a=int) & obj(b=2)), True),
    (lambda: isinstance(obj(a=10, b=2, c=3), temp(a=int) & obj(b=2)), True),
    (lambda: isinstance(obj(a=10, b=3), temp(a=int) & obj(b=2)), False),
)


test_temp_union_annotating = case_of(
    (lambda: isinstance(obj(a=1), temp(a=int) | temp(b=int)), True),
    (lambda: isinstance(obj(b=2), temp(a=int) | temp(b=int)), True),
    (lambda: isinstance(obj(c=3), temp(a=int) | temp(b=int)), False),
    (lambda: isinstance(obj(a=1), temp() | temp(a=int)), True),
    (lambda: isinstance(obj(c=3), temp() | temp(a=int)), True),
    (lambda: isinstance(obj(), temp() | temp(a=int)), True),
    (lambda: isinstance(obj(a=1), temp(a=int) | obj(b=2)), True),
    (lambda: isinstance(obj(b=2), obj(b=2) | temp(a=int)), True),
    (lambda: isinstance(obj(c=3), obj(b=2) | temp(a=int)), False),
)


test_is_templated = case_of(
    (lambda: is_templated('a', 4), False),
    (lambda: is_templated('a', MockA(...)), False),
    (lambda: is_templated('a', obj(a=1, b=2)), False),
    (lambda: is_templated('a', obj()), False),
    (lambda: is_templated('a', temp(a=int, b=int)), True),
    (lambda: is_templated('a', temp(a=int) & obj(b=2)), True),
)


test_templated_attrs_of = case_of(
    (lambda: templated_attrs_of(4), dict()),
    (lambda: templated_attrs_of(MockA(...)), dict()),
    (lambda: templated_attrs_of(obj()), dict()),
    (lambda: templated_attrs_of(obj(a=1, b=2)), dict()),
    (lambda: templated_attrs_of(temp(a=int, b=str)), dict(a=int, b=str)),
    (lambda: templated_attrs_of(temp(a=int, b=str)), dict(a=int, b=str)),
)


test_sculpture_of_getting = case_of(
    (lambda: sculpture_of(MockA(4), b='a').b, 4),
    (lambda: sculpture_of(MockA(4), b=attrgetter('a')).b, 4),
    (
        lambda: with_(raises(AttributeError))(
            lambda _: sculpture_of(MockA(4), b='a').a
        ),
        None,
    ), 
)


def test_sculpture_of_setting():
    original = MockA(4)
    sculpture = sculpture_of(original, a='b')

    sculpture.b = 8

    assert sculpture.b == 8
    assert original.a == 8


@mark.parametrize(
    "value",
    [
        read_only('b'),
        read_only(attrgetter('b')),
        read_only(lambda v: v.c + 2),
        read_only(Access('b', ...)),
    ]
)
def test_read_only_reading(value):
    class WithReadOnly:
        a = read_only(value)
        b = 4
        c = 2


    assert WithReadOnly().a == 4


@mark.parametrize(
    "value",
    [
        read_only('b'),
        read_only(attrgetter('b')),
        read_only(lambda v: v.c + 2),
        read_only(Access('b', ...)),
    ]
)
def test_read_only_setting(value):
    class WithReadOnly:
        a = read_only(value)
        b = 4
        c = 2

    with_read_only = WithReadOnly()

    with raises(AttributeError):
        with_read_only.a = ...
