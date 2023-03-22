from pyhandling.testing import calling_test_case_of


test_calling_test_case_of = calling_test_case_of(
    (lambda: 256, 256),
    (lambda: (lambda a, b: a + b)(60, 4), 64),
    (lambda: (lambda a, b: lambda c: a + b + c)(200, 50)(6), 256),
)
