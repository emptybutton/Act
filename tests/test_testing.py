from pyhandling.testing import calling_test_from, calling_test_of
from pyhandling.tools import ArgumentPack


test_calling_test_from = calling_test_from(
    (lambda: 256, 256),
    (lambda a, b: a + b, 64, ArgumentPack.of(60, 4)),
    (lambda a, b: lambda c: a + b + c, 256, [ArgumentPack.of(50, 6), ArgumentPack.of(200)]),
    (
        lambda a: lambda b: lambda c: lambda d: lambda e: lambda f: a + b + c + d + e + f,
        84,
        [ArgumentPack.of(14)] * 6
    )
)


test_calling_test_of = calling_test_of(
    lambda a, b, c: a + b + c, 256, ArgumentPack.of(200, 50, 6)
)