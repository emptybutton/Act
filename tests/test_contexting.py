from pyhandling.branching import then
from pyhandling.contexting import *
from pyhandling.testing import calling_test_case_of


test_context_oriented = calling_test_case_of(
    (lambda: context_oriented(['val', 'con']), contextual('con', 'val')),
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