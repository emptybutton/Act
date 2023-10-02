from pytest import mark

from act.testing import case_of
from act.tools import *
from tests.mocks import MockA


@mark.parametrize(
    "documentation",
    (
        "Is a handler.", "Is a checker.", "Something.", str(),
        "\n\tIs something.\n\tOr not?", "\tIs a handler.\n\tIs a handler",
    ),
)
def test_documenting_by(documentation: str):
    mock = MockA(None)

    documenting_by(documentation)(mock)

    assert '__doc__' in mock.__dict__.keys()
    assert mock.__doc__ == documentation


test_to_check = case_of(
    (lambda: to_check(4)(4), True),
    (lambda: to_check(4)(8), False),
    (lambda: to_check(bool), bool),
)


test_as_action = case_of(
    (lambda: as_action(4)(1, 2, 3), 4),
    (lambda: as_action(pow)(2, 4), 16),
)
