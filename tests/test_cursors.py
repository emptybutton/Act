from pyhandling.cursors import *
from pyhandling.testing import case_of
from tests.mocks import MockA


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


test_cursors_with_accessing = case_of(
    (lambda: v._(5)(lambda a: a + 3), 8),
    (lambda: v._(2, 6)(pow), 64),
    (lambda: (v[1])('abc'), 'b'),
    (lambda: ('n' + v[1])('abc'), 'nb'),
    (lambda: (v[1] + 'n')('abc'), 'bn'),
    (lambda: (3 * v[1] + 'n')('abc'), 'bbbn'),
    (lambda: (v[w + 1])('abc', 1), 'c'),
    (lambda: (3 * v[w + 1] + 'p')('abc', 1), 'cccp'),
    (lambda: (x * v[w + 1] + y)('abc', 1, 3, 'p'), 'cccp'),
    (lambda: (v.a)(MockA(8)), 8),
    (lambda: (v.a[w])(MockA([1, 2, 3]), -1), 3),
    (lambda: (v.a._(5))(MockA(lambda a: a + 3)), 8),
    (lambda: (2 * v.a._(5) + 16)(MockA(lambda a: a + 3)), 32),
    (lambda: v[w]._(x)([1, lambda x: x + 5, 2], 1, 3), 8),
    (lambda: v._(w + 2)(lambda v: v + 5, 1), 8),
    (lambda: v._(w + 1, 2)(pow, 1), 4),
    (lambda: (v._(w + 1, 2) * 2)(pow, 1), 8),
    (lambda: (8 // v._(w + 1, 2) + 2)(pow, 1), 4),
    (lambda: (v.a.set(4))(MockA(None)).a, 4),
    (lambda: (v.a.set(w))(MockA(6), 16).a, 16),
    (lambda: ((v.a.set(10)).a + w)(MockA(None), 6), 16),
    (lambda: (v.a.set(v.a + 10))(MockA(6)).a, 16),
)
