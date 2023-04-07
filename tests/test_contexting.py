from pyhandling.contexting import *
from pyhandling.flags import nothing
from pyhandling.testing import calling_test_case_of


test_context_oriented = calling_test_case_of(
    (lambda: context_oriented(['val', 'con']), contextual('con', 'val')),
)