from functools import partial
from operator import add, mul, truediv

from act.contexting import contextual, contextually
from act.data_flow import break_
from act.flags import nothing, pointed, flag_about
from act.monads import *
from act.pipeline import then
from act.testing import case_of


test_maybe = case_of(
    (
        lambda: contextual(14, "input context") >= maybe(
            (lambda a: a + 2)
            |then>> (lambda v: contextual(v, bad))
            |then>> (lambda _: "last node result")
        ),
        contextual(16, bad),
    ),
    (
        lambda: contextual(14, "input context") >= maybe(
            (lambda a: a + 2) |then>> (lambda v: contextual(v, bad))
        ),
        contextual(16, bad),
    ),
    (
        lambda: 1 >= maybe(
            (lambda a: a + 1)
            |then>> (lambda _: None)
            |then>> (lambda _: "bad result")
        ),
        contextual(None),
    ),
    (
        lambda: contextual(10, "input context") >= maybe(
            (lambda a: a + 3)
            |then>> (lambda b: b + 2)
            |then>> (lambda c: c + 1)
        ),
        contextual(16, "input context"),
    ),
)


test_until_error = case_of(
    (
        lambda: until_error(lambda a: a + 3)(contextual(1, "input context")),
        contextual(4, "input context"),
    ),
    (
        lambda: until_error((lambda a: a + 1) |then>> (lambda b: b + 2))(
            contextual(1, "input context")
        ),
        contextual(4, "input context"),
    ),
    (
        lambda: contextual(4, "input context") >= (
            until_error(
                (lambda a: a + 2)
                |then>> (lambda b: b / 0)
                |then>> (lambda _: "last node result")
            )
            |then>> (lambda root: (
                root.value,
                tuple(map(lambda context: type(context.point), root.context))
            ))
        ),
        (6, (str, ZeroDivisionError)),
    ),
)


def test_showly():
    logs = list()

    2 >= showly(show=logs.append)(partial(add, 2) |then>> partial(mul, 2))

    assert logs == [4, 8]


test_either = case_of(
    (lambda: either((.1, 1), (.2, 2))(contextual(..., .1)), contextual(1, .1)),
    (lambda: either(('...', -8), (nothing, 8))(...), contextual(8)),
    (lambda: either((0, 0), (1, 16))(contextual(4)), contextual(4)),
    (
        lambda: contextual(4, 2) >= either(
            (lambda c: c > 10, lambda v: v * 10),
            (lambda c: c > 0, lambda v: v * 2),
        ),
        contextual(8, 2),
    ),
    (
        lambda: contextual(6.4, 16) >= either(
            (lambda c: c > 10, lambda v: v * 10),
            (lambda c: c > 0, lambda v: v * 2),
        ),
        contextual(64., 16),
    ),
    (
        lambda: contextual(6.4, 16) >= either(
            (lambda c: c > 10, lambda v: v * 10),
            (lambda c: c > 0, lambda v: v * 2),
        ),
        contextual(64., 16),
    ),
    (
        lambda: contextually(print, 1) >= either(
            (1, lambda v: v),
            (2, lambda _: "bad result"),
        ),
        contextual(print, 1),
    ),
    (
        lambda: contextual(32, 3) >= either(
            (1, lambda _: "first bad result"),
            (2, lambda _: "second bad result"),
            (..., lambda v: v * 2),
        ),
        contextual(64, 3),
    ),
    (
        lambda: contextual(32, 2) >= either(
            (1, "bad result"),
            (2, break_),
            (2, "bad result after \"break\""),
            (..., 8),
        ),
        contextual(8, 2),
    ),
)


def test_in_future():
    some = flag_about("some")

    value, context = in_future(partial(add, 3))(contextual(5, some))

    assert value == 5
    assert context.points[0] is some

    future_actoin, flag = context.points[1]

    assert flag is future
    assert future_actoin() == 8


def test_in_future_with_noncontextual():
    value, context = in_future(partial(truediv, 64))(4)

    assert value == 4

    assert len(context.points) == 1
    assert context.point.context is future
    assert context.point.action() == 16


test_future_from = case_of(
    (lambda: future_from(4), tuple()),
    (lambda: future_from(contextual(4, future)), tuple()),
    (lambda: future_from(contextually(lambda: 4)), tuple()),
    (lambda: future_from(contextually(lambda: 4, future)), (4, )),
    (lambda: future_from(pointed(contextually(lambda: 4, future))), (4, )),
    (lambda: future_from(pointed(1, 2, 3)), tuple()),
    (
        lambda: future_from(pointed(
            contextually(lambda: 4, future),
            contextually(lambda: 8, future),
            contextually(lambda: 16, future),
            "garbage",
        )),
        (4, 8, 16),
    ),
)


test_do_without_actions = case_of(
    (lambda: do()(4), 4),
    (lambda: do()(do.return_(4)), 4),
    (lambda: do()(contextual(4, do.return_ | ok)), contextual(4, ok)),
    (lambda: do.in_form()(4), contextual(4)),
    (lambda: do.in_form()(do.return_(4)), contextual(4)),
    (lambda: do.in_form()(contextual(4, do.return_ | ok)), contextual(4, ok)),
)


test_do_with_one_action = case_of(
    (lambda: do(lambda v: v + 5)(3), 8),
    (lambda: do.in_form(lambda v: v + 5)(3), contextual(8)),
)


def test_do_with_logs():
    logs = list()

    action = do(
        (lambda v: v + 1),
        (lambda v: v - 1) |then>> logs.append,
        logs.append |then>> logs.append,
        (lambda v: v * 10) |then>> (lambda v: v + 4),
    )

    result = action(8)

    assert result == 84
    assert logs == [7, 8, None]


def test_do_return__with_logs():
    logs = list()

    action = do(
        (lambda v: v + 1),
        (lambda v: v - 1) |then>> logs.append,
        (lambda v: v / 2) |then>> do.return_ |then>> (lambda v: -v),
        logs.append |then>> logs.append,
        (lambda v: v * 10) |then>> (lambda v: v + 4),
    )

    result = action(8)

    assert result == 4
    assert logs == [7]


def test_do_in_form_with_logs():
    logs = list()

    action = do.in_form(
        (lambda v: v + 1),
        (lambda v: v - 1) |then>> logs.append,
        logs.append |then>> logs.append,
        (lambda v: v * 10) |then>> (lambda v: v + 4),
    )

    result = action(8)

    assert result == contextual(84)
    assert logs == [7, 8, None]


def test_do_in_form_return__with_logs():
    logs = list()

    action = do.in_form(
        (lambda v: v + 1),
        (lambda v: v - 1) |then>> logs.append,
        (lambda v: v / 2) |then>> do.return_ |then>> (lambda v: -v),
        logs.append |then>> logs.append,
        (lambda v: v * 10) |then>> (lambda v: v + 4),
    )

    result = action(8)

    assert result == contextual(4)
    assert logs == [7]
