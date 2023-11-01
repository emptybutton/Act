from dataclasses import dataclass
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


test_val_creation = case_of(
    (lambda: val().__dict__, dict()),
    (lambda: val(a=1, b=2).__dict__, dict(a=1, b=2)),
    (lambda: val(a=1, b=2), val(a=1, b=2)),
    (lambda: val(a=1, b=2), val(b=2, a=1)),
)


test_val_reconstruction = case_of(
    (lambda: val(a=1) + 'b', val(a=1, b=None)),
    (lambda: val(a=1) + 'a', val(a=1)),
    (lambda: val() + 'a', val(a=None)),
    (lambda: val(a=1, b=2) - 'a', val(b=2)),
    (lambda: val(b=2) - 'a', val(b=2)),
    (lambda: val(b=2) - 'b', val()),
    (lambda: val() - 'b', val()),
)


test_val_sum = case_of(
    (
        lambda: val(MockA(1), MockB(2)),
        val(a=1, b=2),
    ),
    (lambda: val(val(val(a=1))), val(a=1)),
    (lambda: val(a=1) & val(), val(a=1)),
    (lambda: val(a=1) & val(b=2), val(a=1, b=2)),
    (lambda: val(a=1) & val(b=2), val(b=2, a=1)),
    (lambda: val(a=1) & val(a=2), val(a=2)),
    (lambda: val(a=1) & MockB(2), val(a=1, b=2)),
    (lambda: MockA(1) & val(b=2), val(a=1, b=2)),
)


test_val_single_annotating = case_of(
    (lambda: isinstance(MockA(4), val(a=4)), True),
    (lambda: isinstance(MockA(8), val(a=4)), False),
    (lambda: isinstance(val(a=4), val(a=4)), True),
    (lambda: isinstance(val(a=4), val()), True),
    (lambda: isinstance(val(), val()), True),
    (lambda: isinstance(val(a=4, b=2), val(a=4)), True),
    (lambda: isinstance(val(a=4, b=2), val(a=4, b=4)), False),
    (lambda: isinstance(val(a=4, b=2), val(a=4, b=2)), True),
    (lambda: isinstance(MockB(4), val(a=4)), False),
    (lambda: isinstance(MockA(4), val()), True),
    (lambda: isinstance(MockB(4), val()), True),
    (lambda: isinstance(val(a=1, b=2, c=3), val()), True),
    (lambda: isinstance(val(), val()), True),
)


test_val_union_annotating_with_one_attribute = case_of(
    (lambda: isinstance(MockA(1), val(a=1) | val(a=2)), True),
    (lambda: isinstance(MockA(2), val(a=1) | val(a=2)), True),
    (lambda: isinstance(MockA(3), val(a=1) | val(a=2)), False),
    (lambda: isinstance(MockB(3), val(a=1) | val(a=2)), False),
    (lambda: isinstance(val(a=1), val(a=1) | val(a=2)), True),
    (lambda: isinstance(val(a=2), val(a=1) | val(a=2)), True),
    (lambda: isinstance(val(a=3), val(a=1) | val(a=2)), False),
    (lambda: isinstance(val(b=3), val(a=1) | val(a=2)), False),
    (lambda: isinstance(val(a=1, b=3), val(a=1) | val(a=2)), True),
)


test_val_union_annotating_with_multiple_attributes = case_of(
    (lambda: isinstance(val(a=1, b=3), val(a=1) | val(b=2)), True),
    (lambda: isinstance(val(a=0, b=2), val(a=1) | val(b=2)), True),
    (lambda: isinstance(val(a=0, b=0, c=0), val(a=1) | val(b=2)), False),
    (
        lambda: isinstance(
            val(a=0, b=0, c=0),
            val(a=1) | val(b=2, c=2) | val(b=3, c=3),
        ),
        False,
    ),
    (
        lambda: isinstance(
            val(a=0, b=2, c=2),
            val(a=1) | val(b=2, c=2) | val(b=3, c=3),
        ),
        True,
    ),
    (
        lambda: isinstance(
            val(a=1, b=2, c=3, d=40),
            val(a=1) | val(b=2, c=2) | val(b=3, c=3),
        ),
        True,
    ),
    (
        lambda: isinstance(
            val(a=0, b=3, c=3, d=40),
            val(a=1) | val(b=2, c=2) | val(b=3, c=3),
        ),
        True,
    ),
)


test_callable_val = case_of(
    (lambda: callable(val(a=1, b=2)), False),
    (lambda: callable(val(a=1, __call__=lambda _: ...)), True),
    (lambda: val(action=partial(add, 10)).action(6), 16),
    (lambda: val(_=1, __call__=lambda v: v + 5)(3), 8),
)


test_val_with_method = case_of(
    (lambda: val(value=5, method=as_method(lambda o, v: o.value + v)).method(3), 8)
)


test_val_with_descriptor_getting = case_of(
    (lambda: val(a=5, b=as_descriptor(property(lambda o: o.a + 3))).b, 8),
    (lambda: val(a=5, b=as_descriptor(lambda o, v: o.a + v)).b(3), 8),
)


def test_val_with_descriptor_setting():
    valect_ = val(
        a=14,
        b=as_descriptor(property(
            lambda o: o.a + 2,
            lambda o, v: setattr(o, 'a', v * 2),
        )),
    )

    assert valect_.b == 16

    valect_.b = 3

    assert valect_.b == 8


def test_val_with_only_descriptor_setting():
    valect_ = val(
        a=...,
        b=as_descriptor(property(fset=lambda o, v: setattr(o, 'a', v + 10))),
    )

    valect_.b = 6

    assert valect_.a == 16


def test_val_with_only_descriptor_deleting():
    logs = list()

    valect_ = val(
        a=5,
        b=as_descriptor(property(fdel=lambda o: logs.append(o.a + 3))),
    )

    del valect_.b

    assert not hasattr(valect_, 'b')
    assert 'b' in valect_.__dict__.keys()

    assert logs == [8]


test_from_ = case_of(
    (lambda: from_(val(a=1, b=2), val(c=3)), val(a=1, b=2, c=3)),
    (lambda: from_(val(a=2), val(a=1)), val(a=2)),
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


test_to_attr = case_of((
    lambda: to_attr('a', lambda a: a + 5)(MockA(3)).a, 8
))


def test_to_attr_with_immutability():
    val_ = MockA(3)

    result = to_attr('a', lambda a: a + 5)(val_)

    assert isinstance(result, MockA)
    assert result is not val_
    assert result.a == 8


def test_to_attr_with_mutability():
    val_ = MockA(3)

    result = to_attr('a', lambda a: a + 5, mutably=True)(val_)

    assert result is val_
    assert result.a == 8


test_to_attr_without_attribute = case_of((
    lambda: to_attr('b', lambda b: [b])(MockA(3)).b, [None]
))


test_type_creation = case_of(
    (lambda: type(type()), val),
    (lambda: type(a=int)(4).__dict__, dict(a=4)),
    (lambda: type(a=int)(a=4).__dict__, dict(a=4)),
    (lambda: type(a=int, b=int)(4, 8).__dict__, dict(a=4, b=8)),
    (lambda: type(a=int, b=int)(a=4, b=8).__dict__, dict(a=4, b=8)),
    (lambda: type(a=int, b=int)(4, b=8).__dict__, dict(a=4, b=8)),
    (
        lambda: type(a=int, b=int, c=int, d=int, e=int, f=int)(
            1, 2, 3, 4, 5, 6
        ).__dict__,
        dict(a=1, b=2, c=3, d=4, e=5, f=6),
    ),
    (
        lambda: type(a=int, b=int, c=int, d=int, e=int, f=int)(
            a=1, b=2, c=3, d=4, e=5, f=6
        ).__dict__,
        dict(a=1, b=2, c=3, d=4, e=5, f=6),
    ),
    (
        lambda: type(a=int, b=int, c=int, d=int, e=int, f=int)(
            1, 2, 3, d=4, e=5, f=6
        ).__dict__,
        dict(a=1, b=2, c=3, d=4, e=5, f=6),
    ),
)


test_type_comprasion = case_of(
    (lambda: type() == type(), True),
    (lambda: type(a=str) == type(a=str), True),
    (lambda: type(a=str) == type(a=int), False),
    (lambda: type(a=str, b=int) == type(a=int, b=int), False),
    (lambda: type(a=int, b=int, c=int) == type(a=int, b=int), False),
    (lambda: type(a=int, b=int) == type(a=int, b=int, c=int), False),
    (lambda: type(a=int, b=int) == type(), False),
)


test_type_sum = case_of(
    (lambda: type(a=int) & type() == type(a=int), True),
    (lambda: type() & type(b=str) == type(b=str), True),
    (lambda: type(a=int) & type(b=str) == type(a=int, b=str), True),
    (lambda: type(b=str) & type(a=int) == type(a=int, b=str), True),
    (
        lambda: (
            type(a=int, b=int) & type(a=float, c=int)
            == type(a=float, b=int, c=int)
        ),
        True,
    ),
)


test_type_with_values = case_of(
    (lambda: type(type() & val(a=1)), val),
    (lambda: type(val(a=1) & type()), val),
    (lambda: val(a=1) & type(), val(a=1)),
    (lambda: type() & val(a=1), val(a=1)),
    (lambda: type(a=int) & val() == type(a=int), True),
    (lambda: val() & type(a=int) == type(a=int), True),
    (lambda: (type(a=int) & val(b=2))(1), val(a=1, b=2)),
    (
        lambda: (val(a=1) & type(b=int) & val(c=3) & type(d=int))(2, 4),
        val(a=1, b=2, c=3, d=4),
    ),
)


test_type_single_annotating = case_of(
    (lambda: isinstance(MockA(1), type(a=int)), True),
    (lambda: isinstance(MockB(1), type(a=int)), False),
    (lambda: isinstance(val(a=1, b=2), type(a=int, b=int)), True),
    (lambda: isinstance(val(b=2, a=1), type(a=int, b=int)), True),
    (lambda: isinstance(val(c=3, b=2, a=1), type(a=int, b=int)), True),
    (lambda: isinstance(val(c=3, b=2, a=1), type()), True),
    (lambda: isinstance(val(), type()), True),
    (lambda: isinstance(val(a=1), type()), True),
)


test_type_single_annotating_with_values = case_of(
    (lambda: isinstance(val(a=10, b=2), type(a=int) & val(b=2)), True),
    (lambda: isinstance(val(a=10, b=2, c=3), type(a=int) & val(b=2)), True),
    (lambda: isinstance(val(a=10, b=3), type(a=int) & val(b=2)), False),
)


test_type_union_annotating = case_of(
    (lambda: isinstance(val(a=1), type(a=int) | type(b=int)), True),
    (lambda: isinstance(val(b=2), type(a=int) | type(b=int)), True),
    (lambda: isinstance(val(c=3), type(a=int) | type(b=int)), False),
    (lambda: isinstance(val(a=1), type() | type(a=int)), True),
    (lambda: isinstance(val(c=3), type() | type(a=int)), True),
    (lambda: isinstance(val(), type() | type(a=int)), True),
    (lambda: isinstance(val(a=1), type(a=int) | val(b=2)), True),
    (lambda: isinstance(val(b=2), val(b=2) | type(a=int)), True),
    (lambda: isinstance(val(c=3), val(b=2) | type(a=int)), False),
)


test_is_templated = case_of(
    (lambda: is_templated('a', 4), False),
    (lambda: is_templated('a', MockA(...)), False),
    (lambda: is_templated('a', val(a=1, b=2)), False),
    (lambda: is_templated('a', val()), False),
    (lambda: is_templated('a', type(a=int, b=int)), True),
    (lambda: is_templated('a', type(a=int) & val(b=2)), True),
)


test_typelated_attrs_of = case_of(
    (lambda: templated_attrs_of(4), dict()),
    (lambda: templated_attrs_of(MockA(...)), dict()),
    (lambda: templated_attrs_of(val()), dict()),
    (lambda: templated_attrs_of(val(a=1, b=2)), dict()),
    (lambda: templated_attrs_of(type(a=int, b=str)), dict(a=int, b=str)),
    (lambda: templated_attrs_of(type(a=int, b=str)), dict(a=int, b=str)),
)


test_sculpture_of_getting = case_of(
    (lambda: sculpture_of(MockA(4), b='a').b, 4),
    (lambda: sculpture_of(MockA(4), b=attrgetter('a')).b, 4),
    (
        lambda: with_(raises(AttributeError))(
            lambda _: (sculpture_of(MockA(4), b='a') - default_descriptor).a
        ),
        None,
    ),
)


def test_sculpture_of_setting():
    original = MockA(4)
    sculpture = sculpture_of(original, b='a')

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


def test_sculpture_default_descriptor():
    sculpture = sculpture_of(val(a=1, b=2), value='a')

    assert sculpture.value == 1

    assert sculpture.b == 2

    sculpture.b = 4
    assert sculpture.b == 4


def test_struct():
    @dataclass
    class A:
        a: int

    @dataclass
    class B:
        b: str

    assert struct(A) == type(a=int)
    assert struct(A, B) == type(a=int, b=str)


def test_obj():
    object = obj(val(b=4), a=lambda self, a: a * self.b)

    assert object.b == 4
    assert object.a(4) == 16

    assert obj(object) == object
    assert obj(object, {'c': 10}).c == 10
    assert obj(object, val(b=8)).b == 8
    assert (object & val(b=8)).b == 8


def test_namespace():
    @namespace
    class space:
        a: str
        b: str
        all_: str

    assert space.a == 'a'
    assert space.b == 'b'
    assert space.all_ == 'all_'

    assert space.all == ('a', 'b', 'all_')
