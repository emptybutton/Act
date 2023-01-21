from typing import Any, Callable, Optional

from pytest import mark

from pyhandling.annotations import handler_of, checker_of, factory_of, event_for, Handler, Checker, Event


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_handler_of(annotation: Any):
    assert handler_of[annotation] == Callable[[annotation], Any]


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_checker_of(annotation: Any):
    assert checker_of[annotation] == Callable[[annotation], bool]


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_factory_of(annotation: Any):
    assert factory_of[annotation] == Callable[..., annotation]


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_event_for(annotation: Any):
    assert event_for[annotation] == Callable[[], annotation]


def test_Handler():
    assert Handler == handler_of[Any]


def test_Checker():
    assert Checker == checker_of[Any]


def test_Event():
    assert Event == event_for[Any]