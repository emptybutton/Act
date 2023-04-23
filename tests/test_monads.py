from functools import partial
from typing import Any, Iterable, Type, Callable, Mapping, Optional

from pyannotating import number, many_or_one
from pytest import mark, raises

from pyhandling.arguments import ArgumentPack
from pyhandling.annotations import checker_of, event_for
from pyhandling.branching import ActionChain, then
from pyhandling.contexting import contextual
from pyhandling.flags import nothing
from pyhandling.monads import *
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import with_attributes, Logger
from tests.mocks import CustomContext, Counter, MockAction


test_monadically = calling_test_case_of(
    (lambda: tuple(monadically(lambda _: _)(print)), (print, )),
    (lambda: tuple(monadically(lambda _: _)(print |then>> sum)), (print, sum)),
    (
        lambda: (
            monadically(
                lambda action: lambda values: (*values, action(values[-1]))
            )(
                (lambda a: a + 1)
                |then>> (lambda b: b + 2)
                |then>> (lambda c: c + 3)
            )
        )([0]),
        (0, 1, 3, 6),
    ),
)


test_saving_context = calling_test_case_of(
    (
        lambda: saving_context(lambda a: a + 10)(contextual(6, None)),
        contextual(16, None),
    ),
    (
        lambda: saving_context((lambda a: a + 1) |then>> (lambda a: a + 3))(
            contextual(12, None)
        ),
        contextual(16, None),
    ),
)


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