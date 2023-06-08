from pyhandling.error_storing import *
from pyhandling.objects import of
from pyhandling.testing import calling_test_case_of


test_errors_from = calling_test_case_of(
    (lambda: type(errors_from(Exception())[0]), Exception),
    (
        lambda: type(errors_from(of(error=ZeroDivisionError()))[0]),
        ZeroDivisionError,
    ),
    (
        lambda: tuple(map(
            type,
            errors_from(of(TypeError, error=ZeroDivisionError())),
        )),
        (TypeError, ZeroDivisionError),
    ),
    (
        lambda: tuple(map(type, errors_from(of(
            TypeError,
            error=ZeroDivisionError(),
            errors=[
                Exception(),
                of(errors=[KeyError(), ValueError()]),
                of(error=IndexError()),
                of(AttributeError, error=ValueError()),
                of(ZeroDivisionError, errors=tuple()),
                of(
                    TypeError,
                    error=of(Exception, error=IndexError()),
                )
            ],
        )))),
        (
            TypeError, ZeroDivisionError, Exception, KeyError, ValueError,
            IndexError, AttributeError, ValueError, ZeroDivisionError, TypeError,
            Exception, IndexError
        )
    )
)
