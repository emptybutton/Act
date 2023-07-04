from operator import attrgetter

from act.contexting import *
from act.flags import pointed, flag_about
from act.pipeline import then
from act.testing import case_of


test_context_oriented = case_of(
    (lambda: context_oriented(['val', 'con']), contextual('con', 'val')),
)


test_saving_context = case_of(
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


test_to_context = case_of((
    lambda: to_context(lambda c: c * 2)(contextual("value", 4)),
    contextual("value", 8),
))


test_contexted = case_of(
    (lambda: contexted(4), contextual(4)),
    (lambda: contexted(contextual(4)), contextual(4)),
    (lambda: contexted(contextually(print)), contextual(print)),
)


test_contextually = case_of(
    (lambda: contextually(lambda v: v + 3)(5), 8)
)


def test_contextual_error():
    error = Exception()
    error_root = ContextualError(error, 4)

    try:
        raise error_root
    except ContextualError as err:
        assert err == error_root


test_to_write = case_of((
    lambda: to_write(lambda v, c: v + c)(contextual(5, 3)),
    contextual(5, 8)
))


test_to_read = case_of((
    lambda: to_read(lambda v, c: v + c)(contextual(5, 3)),
    contextual(8, 3)
))


test_with_context_that = case_of(
    (
        lambda: with_context_that(lambda c: c > 0, contextual('val', 8)),
        contextual('val', 8),
    ),
    (
        lambda: with_context_that(lambda c: c > 0, contextual('val', -4)),
        contextual('val'),
    ),
    (
        lambda: with_context_that(lambda c: c > 0)(
            contextual('val', pointed(-1, 0, 1, 2))
        ),
        contextual('val', 1),
    ),
)


test_to_metacontextual = case_of(
    (
        lambda: to_metacontextual(lambda v: v * 2, lambda c: c / 2)(
            contextual(1, 2)
        ),
        contextual(2, 1),
    ),
    (
        lambda: to_metacontextual(
            lambda _: print,
            lambda c: c / 2,
            summed=lambda root: contextually(*root),
        )(contextual(..., 2)),
        contextually(print, 1),
    ),
)


test_is_metacontextual = case_of(
    (lambda: is_metacontextual(4), False),
    (lambda: is_metacontextual(contextual(4)), False),
    (lambda: is_metacontextual(contextual(4, ..., ...)), True),
)


test_with_reduced_metacontext = case_of((
    lambda: to_context(attrgetter("points"))(with_reduced_metacontext(
        contextual('val', 'con', 'metacon')
    )),
    contextual('val', ('con', 'metacon')),
))


test_without_metacontext = case_of((
    lambda: to_context(attrgetter("points"))(
        without_metacontext(contextual('val', 1, 2, 3, 4))
    ),
    contextual('val', (1, 2, 3, 4)),
))


def test_be():
    ok = contextualizing(flag_about('ok'))
    bad = contextualizing(flag_about('bad'))

    assert be(ok, 4) == ok(4)
    assert be(ok, contextually(print, ok)) == contextually(print, ok)
    assert be(+ok, ok(4)) == ok(4)
    assert be(+ok, bad(4)) == contextual(4, ok | bad)
    assert be(-ok, ok(4)) == contextual(4)
    assert be(-ok, 4) == contextual(4)


test_of = case_of(
    lambda: of(4)(contextual(..., 4)),
    lambda: not of(4)(contextual(..., 8)),
    lambda: not of(4)(contextual(..., pointed(4))),
    lambda: not of(4)(contextual(..., pointed(6, 8))),
)
