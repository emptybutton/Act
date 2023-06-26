from act.parameter_slicing import *
from act.testing import case_of


test_take = case_of(
    (lambda: take(lambda v=4: v)(1, 2, 3), 4),
    (lambda: take[1](lambda v: v)(1, 4, 8), 4),
    (lambda: take[1][2](lambda v, w: [v, w])(1, 4, 8), [4, 8]),
    (lambda: take[2][1](lambda v, w: [v, w])(1, 4, 8), [8, 4]),
    (lambda: take[1, 2](lambda v, w: [v, w])(1, 4, 8), [4, 8]),
    (lambda: take[0, 1, 2](lambda v, w, x: [v, w, x])(1, 4, 8), [1, 4, 8]),
    (lambda: take['v'](lambda v=4: v)(1, 2, 3), 4),
    (lambda: take['v'](lambda v=2: v)(v=4), 4),
    (lambda: take[0]['w'](lambda v, w: v / w)(16, w=4), 4),
    (lambda: take[0, 'w'](lambda v, w: v / w)(16, w=4), 4),
    (lambda: take[:2](lambda *args: args)(1, 2, 3, 4, 5), (1, 2)),
    (lambda: take[::-1](lambda *args: args)(1, 2, 3), (3, 2, 1)),
    (
        lambda: take[:2]['v'](lambda *args, v: (*args, v))(1, 2, 3, 4, v=-3),
        (1, 2, -3),
    ),
)
