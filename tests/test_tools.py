from pytest import mark

from pyhandling.tools import *
from tests.mocks import MockA


@mark.parametrize(
    "documentation",
    (
        "Is a handler.", "Is a checker.", "Something.", str(),
        "\n\tIs something.\n\tOr not?", "\tIs a handler.\n\tIs a handler",
    )
)
def test_documenting_by(documentation: str):
    mock = MockA(None)

    documenting_by(documentation)(mock)

    assert '__doc__' in mock.__dict__.keys()
    assert mock.__doc__ == documentation
