from pyhandling.error_storing import *
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import with_attributes


test_errors_from = calling_test_case_of(
    (lambda: type(errors_from(Exception())[0]), Exception),
    (
        lambda: type(errors_from(with_attributes(error=ZeroDivisionError()))[0]),
        ZeroDivisionError,
    ),
    (
        lambda: tuple(map(
            type,
            errors_from(with_attributes(TypeError, error=ZeroDivisionError())),
        )),
        (TypeError, ZeroDivisionError),
    ),
    (
        lambda: tuple(map(type, errors_from(with_attributes(
            TypeError,
            error=ZeroDivisionError(),
            errors=[
                Exception(),
                with_attributes(errors=[KeyError(), ValueError()]),
                with_attributes(error=IndexError()),
                with_attributes(AttributeError, error=ValueError()),
                with_attributes(ZeroDivisionError, errors=tuple()),
                with_attributes(
                    TypeError,
                    error=with_attributes(Exception, error=IndexError()),
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
