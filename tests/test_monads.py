from functools import partial
from typing import Any, Iterable, Type, Callable, Mapping, Optional

from pyannotating import number, many_or_one
from pytest import mark, raises

from pyhandling.arguments import ArgumentPack
from pyhandling.annotations import checker_of, event_for
from pyhandling.branching import ActionChain
from pyhandling.contexting import contextual
from pyhandling.flags import nothing
from pyhandling.monads import *
from pyhandling.synonyms import with_context_by
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import with_attributes, Logger
from tests.mocks import CustomContext, Counter, MockAction


# @mark.parametrize(
#     "number_of_handlers, number_of_writer_calls",
#     tuple(map(
#         lambda number: (number, number),
#         (*range(0, 4), 32, 64, 128, 516)
#     ))
# )
# def test_showly_by_logger(number_of_handlers: int, number_of_writer_calls: int):
#     writing_counter = Counter()

#     showly(
#         (
#             MockAction()
#             if number_of_handlers == 1
#             else ActionChain((MockAction(), ) * number_of_handlers)
#         ),
#         show=lambda _: writing_counter()
#     )(None)

#     assert writing_counter.counted == number_of_writer_calls


test_monadically = calling_test_case_of(
    (lambda: tuple(monadically(lambda _: _)(print)), (print, )),
    (lambda: tuple(monadically(lambda _: _)([print, sum])), (print, sum)),
    (
        lambda: (
            monadically(
                lambda action: lambda values: (*values, action(values[-1]))
            )(
                [lambda a: a + 1, lambda b: b + 2, lambda c: c + 3]
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
        lambda: saving_context([lambda a: a + 1, lambda a: a + 3])(
            contextual(12, None)
        ),
        contextual(16, None),
    ),
)


test_maybe = calling_test_case_of(
    (
        lambda: contextual(14, when="input context") >= maybe([
            lambda a: a + 2, partial(contextual, when=bad), lambda _: "last node result"
        ]),
        contextual(16, bad),
    ),
    (
        lambda: contextual(10, when="input context") >= maybe([
            lambda a: a + 3, lambda b: b + 2, lambda c: c + 1
        ]),
        contextual(16, when="input context"),
    ),
)


test_until_error = calling_test_case_of(
    (
        lambda: until_error(lambda a: a + 3)(contextual(1, "input context")),
        contextual(4, "input context"),
    ),
    (
        lambda: until_error([lambda a: a + 1, lambda b: b + 2])(
            contextual(1, "input context")
        ),
        contextual(4, "input context"),
    ),
    (
        lambda: (lambda root: (root.value, type(tuple(root.context)[0].point)))(
            until_error([
                lambda a: a + 2, lambda b: b / 0, lambda _: "last node result"
            ])(contextual(4, when="input context"))
        ),
        (6, ZeroDivisionError),
    ),
)