from functools import partial
from typing import Mapping, Any

from pytest import mark

from pyhandling.aggregates import *
from pyhandling.testing import case_of


@partial(mark.parametrize, "kwargs")([
    dict(), dict(lift=str), dict(is_lifted=bool), dict(lift=str, is_lifted=bool)
])
def test_effect_partiality(kwargs: Mapping[str, Any]):
    effect = Effect(**kwargs)

    assert isinstance(effect, partial)
    assert effect.args == tuple()
    assert effect.keywords == kwargs
    assert effect.func is Effect


test_effect_creation = case_of(
    (lambda: type(Effect(lambda _: _, lift=str, is_lifted=bool)), Effect),
    (lambda: type(Effect()(lambda _: _, lift=str, is_lifted=bool)), Effect),
    (lambda: type(Effect(lift=str)(lambda _: _, is_lifted=bool)), Effect),
    (lambda: type(Effect(lift=str, is_lifted=bool)(lambda _: _)), Effect),
)


def test_effect_application():
    effect = Effect(
        lambda action: lambda line: action(float(line)),
        lift=str,
        is_lifted=lambda v: isinstance(v, str),
    )

    effect_by_partiality = Effect(
        lift=str,
        is_lifted=lambda v: isinstance(v, str),
    )(
        lambda action: lambda line: action(float(line))
    )

    assert (
        effect(lambda v: v + 5)('3')
        == effect(lambda v: v + 5, '3')
        == effect_by_partiality(lambda v: v + 5)('3')
        == effect_by_partiality(lambda v: v + 5, '3')
        == '8.0'
    )


def test_effect_lifted():
    effect = Effect(
        lambda _: _,
        lift=lambda v: str(v) + '4',
        is_lifted=lambda v: isinstance(v, str),
    )

    assert effect.lifted(4) == '44'
    assert effect.lifted('4') == '4'


def test_effect_by():
    old_effect = Effect(lambda _: _, lift=lambda _: _, is_lifted=lambda _: True)
    new_effect = old_effect.by(lambda dec: lambda func: lambda v: dec(func)(str(v)))

    assert [8] == old_effect(lambda v: [v], 8)
    assert ['8'] == new_effect(lambda v: [v], 8)


def test_as_effect_with_effect():
    effect = Effect(lambda _: _, lift=lambda _: _, is_lifted=lambda _: True)
    assert as_effect(effect) is effect


def test_as_effect_without_effect():
    effect = as_effect(lambda _: _)

    assert type(effect) is Effect
    assert effect.is_lifted(8)
    assert 8 == effect(lambda v: v + 5, 3)
