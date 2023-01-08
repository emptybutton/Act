from typing import Callable, Optional

from pytest import mark

from pyhandling.annotations import handler_of, checker_of, factory_of, event_for, Handler, Checker, Event


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_handler_of(annotation: any):
    assert handler_of[annotation] == Callable[[annotation], any]


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_checker_of(annotation: any):
    assert checker_of[annotation] == Callable[[annotation], bool]


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_factory_of(annotation: any):
    assert factory_of[annotation] == Callable[..., annotation]


@mark.parametrize('annotation', (object, int, float, None, Ellipsis, int | float, Optional[str]))
def test_event_for(annotation: any):
    assert event_for[annotation] == Callable[[], annotation]


def test_Handler():
    assert Handler == handler_of[any]


def test_Checker():
    assert Checker == checker_of[any]


def test_Event():
    assert Event == event_for[any]