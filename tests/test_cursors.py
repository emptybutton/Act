from functools import reduce
import operator

from act.cursors import *
from act.testing import case_of
from tests.mocks import MockA, MockB

from pytest import mark


test_single_cursor = case_of((
    lambda: (v)(8), 8,
))


test_cursors_with_operators = case_of(
    (lambda: (+v)(8), 8),
    (lambda: (-v)(8), -8),
    (lambda: (~v)(7), -8),
    (lambda: (v + 5)(3), 8),
    (lambda: (5 + v)(3), 8),
    (lambda: (-v + 4)(4), 0),
    (lambda: (4 + (-v))(4), 0),
    (lambda: (1 + v + 5)(2), 8),
    (lambda: (v - 10)(18), 8),
    (lambda: (18 - v)(10), 8),
    (lambda: ((18 - v) * 2)(14), 8),
    (lambda: (v * 16)(4), 64),
    (lambda: (16 * v)(4), 64),
    (lambda: (16 * (-v))(-4), 64),
    (lambda: (v / 2)(16), 8),
    (lambda: (16 / v)(2), 8),
    (lambda: (v / 2 + 5)(6), 8),
    (lambda: (6 + v / 2)(4), 8),
    (lambda: (v // 2 * 2)(10.5), 10),
    (lambda: (v | int)(float), int | float),
    (lambda: (v | int | set)(float), float | int | set),
    (lambda: (str | v)(float), str | float),
    (lambda: (str | v | int)(float), str | float | int),
    (lambda: (str | v | int | set)(float), str | float | int | set),
    (lambda: (((2 + v * 2) / 2) ** 2)(2), 9),
    (lambda: (v % 2)(4.5), 0.5),
    (lambda: (v >> 1)(10), 5),
    (lambda: (10 >> v)(1), 5),
    (lambda: (v << 1)(10), 20),
    (lambda: (10 << v)(1), 20),
    (lambda: (v >> 1 << 1)(10), 10),
    (lambda: (v ^ {1, 2, 3})({0, 1, 2}), {0, 3}),
    (lambda: ({1, 2, 3} ^ v)({0, 1, 2}), {0, 3}),
    (lambda: ((v + w) * (v - w))(4, 2), 12),
)


test_cursor_order = case_of(
    (
        lambda: (
            a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + q
            + r + s + t + u + v + w + x + y + z
        )(
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
        ),
        "abcdefghijklmnopqrstuvwxyz",
    ),
    (
        lambda: (
            z + y + x + w + v + u + t + s + r + q + p + o + n + m + l + k + j
            + i + h + g + f + e + d + c + b + a
        )(
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
        ),
        "zyxwvutsrqponmlkjihgfedcba",
    ),
)


test_cursors_with_calling = case_of(
    (lambda: v._(5)(lambda a: a + 3), 8),
    (lambda: v._(2, 6)(pow), 64),
    (lambda: v._(w + 2)(lambda v: v + 5, 1), 8),
    (lambda: v._(w + 1, 2)(pow, 1), 4),
    (lambda: (v._(w + 1, 2) * 2)(pow, 1), 8),
    (lambda: (8 // v._(w + 1, 2) + 2)(pow, 1), 4),
)


test_cursors_with_item_getting = case_of(
    (lambda: (v[1])('abc'), 'b'),
    (lambda: ('n' + v[1])('abc'), 'nb'),
    (lambda: (v[1] + 'n')('abc'), 'bn'),
    (lambda: (3 * v[1] + 'n')('abc'), 'bbbn'),
    (lambda: (v[w + 1])('abc', 1), 'c'),
    (lambda: (3 * v[w + 1] + 'p')('abc', 1), 'cccp'),
    (lambda: (x * v[w + 1] + y)('abc', 1, 3, 'p'), 'cccp'),
    (lambda: v[w]._(x)([1, lambda x: x + 5, 2], 1, 3), 8),
)


test_cursors_with_item_setting = case_of(
    (lambda: l[1].set(l[1] + 10)([1, 2, 3]), [1, 12, 3]),
    (lambda: t[1].set(t[1] + 10)((1, 2, 3)), (1, 12, 3)),
    (lambda: l[1].be(i + 10)([1, 2, 3]), [1, 12, 3]),
    (lambda: t[1].be(i + 10)((1, 2, 3)), (1, 12, 3)),
)


def test_cursor_item_setting_immutability():
    object_ = [1, 2, 3]

    new_object_ = (v[1].set(-2))(object_)

    assert object_ is not new_object_
    assert object_ == [1, 2, 3]
    assert new_object_ == [1, -2, 3]


def test_cursor_item_setting_mutability():
    object_ = [1, 2, 3]

    new_object_ = (v[1].mset(-v[1]))(object_)

    assert object_ is new_object_
    assert object_ == new_object_ == [1, -2, 3]


test_cursors_with_attr_getting = case_of(
    (lambda: (v.a)(MockA(8)), 8),
    (lambda: (v.a[w])(MockA([1, 2, 3]), -1), 3),
    (lambda: (v.a._(5))(MockA(lambda a: a + 3)), 8),
    (lambda: (2 * v.a._(5) + 16)(MockA(lambda a: a + 3)), 32),
)


test_cursors_with_attr_setting = case_of(
    (lambda: (v.a.set(4))(MockA(None)).a, 4),
    (lambda: (v.a.set(w))(MockA(6), 16).a, 16),
    (lambda: ((v.a.set(10)).a + w)(MockA(None), 6), 16),
    (lambda: (v.a.set(v.a + 10))(MockA(6)).a, 16),
    (lambda: o.a.be(abs)(MockA(a=-8)).a, 8),
    (lambda: o.a.be(a**2)(MockA(a=4)).a, 16),
)


def test_cursor_attr_setting_immutability():
    object_ = MockA(None)

    new_object_ = (v.a.set(4))(object_)

    assert object_ is not new_object_
    assert object_.a is None
    assert new_object_.a == 4


def test_cursor_mutable_attr_setting():
    object_ = MockA(None)

    new_object_ = (v.a.mset(4))(object_)

    assert object_ is new_object_
    assert object_.a == new_object_.a == 4


test_external_cursors = case_of(
    (lambda: _()(), tuple()),
    (lambda: _(1)(), (1, )),
    (lambda: _(1, 2, 3)(), (1, 2, 3)),
    (lambda: _(6, v + 2, v + 3)(5), (6, 7, 8)),
    (lambda: _(6, v + w, v + x)(5, 2, 3), (6, 7, 8)),
    (lambda: _[1](), [1]),
    (lambda: _[1, 2, 3](), [1, 2, 3]),
    (lambda: _[6, v + 2, v + 3](5), [6, 7, 8]),
    (lambda: _[6, v + w, v + x](5, 2, 3), [6, 7, 8]),
    (lambda: _.pow(v, w + 1)(2, 2), 8),
    (lambda: _.operator.eq(v, w + 1)(1, 0), True),
    (lambda: act()(), tuple()),
    (lambda: act(1)(), (1, )),
    (lambda: act(1, 2, 3)(), (1, 2, 3)),
    (lambda: act(6, v + 2, v + 3)(5), (6, 7, 8)),
    (lambda: act(6, v + w, v + x)(5, 2, 3), (6, 7, 8)),
    (lambda: act[1](), [1]),
    (lambda: act[1, 2, 3](), [1, 2, 3]),
    (lambda: act[6, v + 2, v + 3](5), [6, 7, 8]),
    (lambda: act[6, v + w, v + x](5, 2, 3), [6, 7, 8]),
    (lambda: act.pow(v, w + 1)(2, 2), 8),
    (lambda: act.operator.eq(v, w + 1)(1, 0), True),
)


@mark.parametrize("cursor", [_, act])
def test_external_cursor_vargetting(cursor):
    value = 5

    assert (cursor.value + 3)() == 8
    assert (cursor.value + v)(3) == 8

    actions = [operator.eq, operator.add]
    actions.append(actions)

    assert cursor.actions[0](1, 1)()
    assert not cursor.actions[0](1, 2)()

    assert cursor.actions[0](v + w, v - w)(4, 0)
    assert not cursor.actions[0](v + w, v - w)(4, 1)

    assert (-(w*cursor.actions[2][2][2][1](v + w, v - w)) - v)(4, 2) == -20

    action_boxes = [MockA(lambda a_: a_ + 5), MockB([1, lambda b_: b_ + 3])]

    assert (cursor.action_boxes[0].a(v * 2) + w)(5, 1) == 16
    assert (cursor.action_boxes[1].b[1](w * 2) + v)(3, 5) == 16


test_cursor_comparison_operators = case_of(
    (lambda: (v == w)(1, 1), True),
    (lambda: (v == w)(1, 2), False),
    (lambda: _[v == w, v, w](1, 2), [False, 1, 2]),
    (lambda: (v != w)(1, 2), True),
    (lambda: (v != w)(1, 1), False),
    (lambda: (v - 1 > w + 1)(4, 1), True),
    (lambda: (v - 1 > w + 1)(3, 1), False),
    (lambda: (v - 1 >= w + 1)(3, 1), True),
    (lambda: (v - 1 >= w + 1)(4, 1), True),
    (lambda: (w + 1 < v - 1)(4, 1), True),
    (lambda: (w + 1 < v - 1)(3, 1), False),
    (lambda: (w + 1 <= v - 1)(3, 1), True),
    (lambda: (w + 1 <= v - 1)(4, 1), True),
)


test_cursor_comparison_methods = case_of(
    (lambda: v.is_(w)(None, None), True),
    (lambda: v.is_(w)(True, False), False),
    (lambda: v.is_not(w)(True, False), True),
    (lambda: v.is_not(w)(None, None), False),
    (lambda: v.in_(w)(1, [1, 2]), True),
    (lambda: w.in_(v)([1, 2], 1), True),
    (lambda: v.in_(w)(1, [2, 3]), False),
    (lambda: w.in_(v)([2, 3], 1), False),
    (lambda: v.not_in(w)(1, [2, 3]), True),
    (lambda: w.not_in(v)([2, 3], 1), True),
    (lambda: v.not_in(w)(1, [1, 2]), False),
    (lambda: w.not_in(v)([1, 2], 1), False),
    (lambda: v.contains(w)([1, 2], 1), True),
    (lambda: w.contains(v)(1, [1, 2]), True),
    (lambda: v.contains(w)([2, 3], 1), False),
    (lambda: w.contains(v)(1, [2, 3]), False),
    (lambda: v.contains_no(w)([2, 3], 1), True),
    (lambda: w.contains_no(v)(1, [2, 3]), True),
    (lambda: v.contains_no(w)([1, 2], 1), False),
    (lambda: w.contains_no(v)(1, [1, 2]), False),
    (lambda: v.and_(w)(1, 2), 2),
    (lambda: v.and_(w)(1, 0), 0),
    (lambda: v.and_(w)(0, 1), 0),
    (lambda: v.or_(w)(1, 2), 1),
    (lambda: v.or_(w)(1, 0), 1),
    (lambda: v.or_(w)(0, 1), 1),
    (
        lambda: _[v.is_(w), w.is_not(v), v.and_(w), w.or_(v)](0, 1),
        [False, True, 0, 1],
    ),
    (lambda: v.is_(w).or_(w.in_(v))([0, 1], 1), True),
)


test_cursor_unpacking = case_of(
    (
        lambda: _(0, v, *w, 4, *x, y, 8)(1, [2, 3], [5, 6], 7),
        (0, 1, 2, 3, 4, 5, 6, 7, 8),
    ),
    (
        lambda: _[0, v, *w, 4, *x, y, 8](1, [2, 3], [5, 6], 7),
        [0, 1, 2, 3, 4, 5, 6, 7, 8],
    ),
    (lambda: _.reduce(v, _(1, *w))(operator.add, [2, 3, 4]), 10),
    (lambda: _.dict(**(v | w))(dict(a=1, b=1), dict(b=2)), dict(a=1, b=2)),
)


test_unlimited_argument_cursors = case_of(
    (lambda: args(), tuple()),
    (lambda: args(1, 2, 3), (1, 2, 3)),
    (lambda: _(v, *args)(0, 1, 2, 3), (0, 1, 2, 3)),
    (lambda: (v + args)((0, 1), 2, 3), (0, 1, 2, 3)),
    (lambda: (v + args)((0, 1)), (0, 1)),
    (lambda: (args + _(v,  w))(2, 3, 0, 1), (0, 1, 2, 3)),
    (lambda: (v | kwargs)(dict(a=1, b=1), b=2), dict(a=1, b=2)),
    (lambda: (v | kwargs)(dict(a=1, b=2)), dict(a=1, b=2)),
)


test_cursot_partiality = case_of(
    (lambda: (v)()()()(8), 8),
    (lambda: (v + w)()()()(5)()()()(3), 8),
    (lambda: (v / w + x)(10)(2)(3), 8),
    (lambda: (v / w + x)(10, 2)(3), 8),
    (lambda: (v / w + x)(10)(2, 3), 8),
)
