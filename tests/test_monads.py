from pyhandling.branching import then
from pyhandling.contexting import contextual
from pyhandling.monads import *
from pyhandling.testing import case_of


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
        lambda: (lambda root: (
            root.value,
            tuple(map(lambda context: type(context.point), root.context))
        ))(
            contextual(4, "input context") >= until_error(
                (lambda a: a + 2)
                |then>> (lambda b: b / 0)
                |then>> (lambda _: "last node result")
            )
        ),
        (6, (str, ZeroDivisionError)),
    ),
)
