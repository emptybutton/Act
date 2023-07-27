from operator import attrgetter

from act.contexting import *
from act.flags import pointed, flag_about, nothing
from act.pipeline import then
from act.testing import case_of


test_context_oriented = case_of(
    (lambda: context_oriented(4), contextual(4, nothing)),
    (lambda: context_oriented(contextual('con', 'val')), contextual('val', 'con')),
    (
        lambda: context_oriented(contextually(print, 'con')),
        contextual('con', print),
    ),
)


test_saving_context = case_of(
    (
        lambda: saving_context(lambda a: a + 10)(contextual(None, 6)),
        contextual(None, 16),
    ),
    (
        lambda: saving_context((lambda a: a + 1) |then>> (lambda a: a + 3))(
            contextual(None, 12)
        ),
        contextual(None, 16),
    ),
)


test_to_context = case_of((
    lambda: to_context(lambda c: c * 2)(contextual(4, "value")),
    contextual(8, "value"),
))


test_nested_contextual = case_of(
    (lambda: contextual(1, 2, 4), contextual(1, contextual(2, 4))),
)


test_contexted = case_of(
    (lambda: contexted(4), contextual(4)),
    (lambda: contexted(contextual(4)), contextual(4)),
    (lambda: contexted(contextually(print)), contextual(print)),
)


test_contextually = case_of(
    (lambda: contextually(lambda v: v + 3)(5), 8),
    (lambda: contextually(2, 1, lambda v: v + 3)(5), 8)
)


def test_contextual_error():
    error = Exception()
    error_root = ContextualError(4, error)

    try:
        raise error_root
    except ContextualError as err:
        assert err == error_root


test_to_write = case_of((
    lambda: to_write(lambda v, c: v + c)(contextual(3, 5)),
    contextual(8, 5)
))


test_to_read = case_of((
    lambda: to_read(lambda v, c: v + c)(contextual(3, 5)),
    contextual(3, 8)
))


test_with_context_that = case_of(
    (
        lambda: with_context_that(lambda c: c > 0, contextual(8, 'val')),
        contextual(8, 'val'),
    ),
    (
        lambda: with_context_that(lambda c: c > 0, contextual(-4, 'val')),
        contextual('val'),
    ),
    (
        lambda: with_context_that(lambda c: c > 0)(
            contextual(pointed(-1, 0, 1, 2), 'val')
        ),
        contextual(1, 'val'),
    ),
)


test_to_metacontextual = case_of(
    (
        lambda: to_metacontextual(lambda c: c / 2, lambda v: v * 2)(
            contextual(2, 1)
        ),
        contextual(1, 2),
    ),
    (
        lambda: to_metacontextual(
            lambda c: c / 2,
            lambda _: print,
            summed=lambda root: contextually(*root),
        )(contextual(2, ...)),
        contextually(1, print),
    ),
)


test_is_metacontextual = case_of(
    (lambda: is_metacontextual(4), False),
    (lambda: is_metacontextual(contextual(4)), False),
    (lambda: is_metacontextual(contextual(..., ..., 4)), True),
)


test_with_reduced_metacontext = case_of((
    lambda: to_context(attrgetter("points"))(with_reduced_metacontext(
        contextual('metacon', 'con', 'val')
    )),
    contextual(('metacon', 'con'), 'val'),
))


test_without_metacontext = case_of((
    lambda: to_context(attrgetter("points"))(
        without_metacontext(contextual(1, 2, 3, 4, 'val'))
    ),
    contextual((1, 2, 3, 4), 'val'),
))


def test_be():
    ok = contextualizing(flag_about('ok'))
    bad = contextualizing(flag_about('bad'))

    assert be(ok, 4) == ok(4)
    assert be(ok, contextually(ok, print)) == contextually(ok, print)
    assert be(+ok, ok(4)) == ok(4)
    assert be(+ok, bad(4)) == contextual(ok | bad, 4)
    assert be(-ok, ok(4)) == contextual(4)
    assert be(-ok, 4) == contextual(4)


test_of = case_of(
    lambda: of(4)(contextual(4, ...)),
    lambda: not of(4)(contextual(8, ...)),
    lambda: not of(4)(contextual(pointed(4), ...)),
    lambda: not of(4)(contextual(pointed(6, 8), ...)),
)
