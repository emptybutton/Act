from pytest import raises

from act.contexting import contextual
from act.error_flow import *
from act.synonyms import with_
from act.testing import case_of


test_raising = case_of(
    lambda: with_(raises(ValueError), raising(ValueError())),
    lambda: with_(raises(IndexError), raising(IndexError())),
)


test_catching = case_of(
    (lambda: catching(ValueError, type, ValueError()), ValueError),
    (lambda: catching(IndexError, type, IndexError()), IndexError),
    (lambda: catching(IndexError, type)(IndexError()), IndexError),
    lambda: with_(
        raises(ValueError),
        lambda _: catching(IndexError, lambda _: "Bad result", ValueError),
    ),
)


test_with_error = case_of(
    (
        lambda: (lambda result: (result.value, type(result.context)))(
            with_error(raising(TypeError()))(...)
        ),
        (None, TypeError),
    ),
    (lambda: with_error(lambda v: v + 4)(4), contextual(8)),
)
