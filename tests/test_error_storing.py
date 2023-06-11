from pyhandling.error_storing import *
from pyhandling.objects import obj, of
from pyhandling.testing import case_of


test_errors_from = case_of(
    (lambda: type(errors_from(Exception())[0]), Exception),
    (
        lambda: type(errors_from(obj(error=ZeroDivisionError()))[0]),
        ZeroDivisionError,
    ),
    (
        lambda: tuple(map(
            type,
            errors_from(of(obj(error=ZeroDivisionError()), TypeError())),
        )),
        (TypeError, ZeroDivisionError),
    ),
    (
        lambda: tuple(map(type, errors_from(of(obj(
            error=ZeroDivisionError(),
            errors=[
                Exception(),
                obj(errors=[KeyError(), ValueError()]),
                obj(error=IndexError()),
                of(obj(error=ValueError()), AttributeError()),
                of(obj(errors=tuple()), ZeroDivisionError()),
                of(
                    obj(error=of(obj(error=IndexError()), Exception())),
                    TypeError(),
                ),
            ],
        ))(TypeError())))),
        (
            TypeError, ZeroDivisionError, Exception, KeyError, ValueError,
            IndexError, AttributeError, ValueError, ZeroDivisionError, TypeError,
            Exception, IndexError
        )
    )
)
