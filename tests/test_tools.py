from pytest import mark

from pyhandling.objects import obj
from pyhandling.tools import *


@mark.parametrize(
    "documentation",
    (
        "Is a handler.", "Is a checker.", "Something.", str(),
        "\n\tIs something.\n\tOr not?", "\tIs a handler.\n\tIs a handler",
    )
)
def test_documenting_by(documentation: str):
    mock = obj()

    documenting_by(documentation)(mock)

    assert '__doc__' in mock.__dict__.keys()
    assert mock.__doc__ == documentation
