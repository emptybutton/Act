from act.operators import *
from act.testing import case_of


test_are_linear = case_of(
    (lambda: are_linear([1, 2, 3, 4, 5], lambda a, b: a + 1 == b), True),
    (lambda: are_linear([1, 2, 3.5, 4, 5], lambda a, b: a + 1 == b), False),
    (lambda: are_linear([4, 2, 3], lambda a, b: a + 1 == b, sum_=any), True),
)


test_inclusive_all = case_of(
    (lambda: inclusive_all([True] * 3), True),
    (lambda: inclusive_all((False, False)), False),
    (lambda: inclusive_all(tuple()), False),
)


test_not_inclusive_any = case_of(
    (lambda: not_inclusive_any((False, True, False)), True),
    (lambda: not_inclusive_any((False, False)), False),
    (lambda: not_inclusive_any(tuple()), True),
)


test_not_ = case_of(
    (lambda: bool(not_(4)), False),
    (lambda: bool(not_(0)), True),
    (lambda: not_(lambda n: n > 0)(2), False),
    (lambda: not_(lambda n: n > 0)(-2), True),
    (lambda: not_(4)(4), False),
    (lambda: not_(4)(2), True),
)


test_or_ = case_of(
    (lambda: bool(or_(0, 1, 0)), True),
    (lambda: bool(or_(False, False, False)), False),
    (lambda: or_(lambda n: isinstance(n, float), lambda n: n > 0)(4), True),
    (lambda: or_(lambda n: isinstance(n, float), lambda n: n > 0)(-1.6), True),
    (lambda: or_(lambda n: isinstance(n, float), lambda n: n > 0)(-16), False),
    (lambda: or_(2, 4, 8)(4), True),
    (lambda: or_(2, 4)(3), False),
)


test_and_ = case_of(
    (lambda: bool(and_(1, 2, 3)), True),
    (lambda: bool(and_(False, True, False)), False),
    (lambda: and_(lambda n: 0 < n, lambda n: n <= 10)(4), True),
    (lambda: and_(lambda n: 0 < n, lambda n: n <= 10)(-4), False),
    (lambda: and_(2, 2.)(2), True),
    (lambda: and_(2, 2.)(3), False),
)


test_div = case_of(
    (lambda: div(64, 16), 4.0),
)
