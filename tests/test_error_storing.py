from act.error_storing import *
from act.objects import obj, from_
from act.testing import case_of


test_errors_from = case_of(
    (lambda: type(errors_from(Exception())[0]), Exception),
    (
        lambda: type(errors_from(obj(error=ZeroDivisionError()))[0]),
        ZeroDivisionError,
    ),
    (
        lambda: tuple(map(
            type,
            errors_from(from_(obj(error=ZeroDivisionError()), TypeError())),
        )),
        (TypeError, ZeroDivisionError),
    ),
    (
        lambda: tuple(map(type, errors_from(from_(obj(
            error=ZeroDivisionError(),
            errors=[
                Exception(),
                obj(errors=[KeyError(), ValueError()]),
                obj(error=IndexError()),
                from_(obj(error=ValueError()), AttributeError()),
                from_(obj(errors=tuple()), ZeroDivisionError()),
                from_(
                    obj(error=from_(obj(error=IndexError()), Exception())),
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
