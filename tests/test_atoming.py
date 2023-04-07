from pyhandling.atoming import *
from pyhandling.branching import ActionChain
from pyhandling.testing import calling_test_case_of


test_atomically = calling_test_case_of(
    (lambda: isinstance(atomically(ActionChain([int, str])), ActionChain), False),
    (lambda: len(tuple(ActionChain([atomically(ActionChain([int, str])), print]))), 2),
    (lambda: atomically(lambda a: a)(4), 4)
)