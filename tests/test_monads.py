from functools import partial

from pyhandling.branching import then
from pyhandling.contexting import contextual
from pyhandling.monads import *
from pyhandling.testing import calling_test_case_of


test_maybe = calling_test_case_of(
    (
        lambda: contextual(14, when="input context") >= maybe(
            (lambda a: a + 2)
            |then>> partial(contextual, when=bad)
            |then>> (lambda _: "last node result")
        ),
        contextual(16, bad),
    ),
    (
        lambda: contextual(10, when="input context") >= maybe(
            (lambda a: a + 3)
            |then>> (lambda b: b + 2)
            |then>> (lambda c: c + 1)
        ),
        contextual(16, when="input context"),
    ),
)


test_until_error = calling_test_case_of(
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
        lambda: (lambda root: (
            root.value,
            tuple(map(lambda context: type(context.point), root.context))
        ))(
            contextual(4, when="input context") >= until_error(
                (lambda a: a + 2)
                |then>> (lambda b: b / 0)
                |then>> (lambda _: "last node result")
            )
        ),
        (6, (str, ZeroDivisionError)),
    ),
)
