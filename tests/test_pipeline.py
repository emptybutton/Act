from typing import Iterable, Callable, Any

from act.pipeline import *
from act.testing import case_of
from tests.mocks import MockAction

from pytest import mark


test_action_chain_calling = case_of(
    (lambda: ActionChain([lambda x: x + 2, lambda x: x ** x])(2), 256),
    (lambda: ActionChain([lambda _: None])(256), None),
    (lambda: ActionChain()(None), None),
)


@mark.parametrize(
    'first_nodes, second_nodes',
    [
        [(MockAction(), lambda x: x + 1), (MockAction(), MockAction())],
        [(MockAction(), lambda x: x + 1, MockAction()), (MockAction(), )],
        [(MockAction(), ), (MockAction(), MockAction())],
        [(MockAction(), lambda x: x + 1), tuple()],
        [tuple(), (MockAction(), )],
        [tuple(), tuple()],
        [ActionChain([int, ActionChain([float, str])]), (int, float, str)],
    ]
)
def test_action_chain_iteration(
    first_nodes: Iterable[Callable[Any, Any]],
    second_nodes: Iterable[Callable[Any, Any]],
):
    assert (
        tuple(ActionChain((*first_nodes, *second_nodes)))
        == (*first_nodes, *second_nodes)
    )


test_action_inserting_in = case_of(
    (lambda: bind_by([..., (lambda b: b / 2)])(lambda a: a + 3)(13), 8),
    (lambda: bind_by([(lambda a: a + 3), ...])(lambda b: b / 2)(13), 8),
    (lambda: bind_by([..., ...])(lambda a: a + 2)(12), 16)
)


test_bind = case_of(
    (lambda: bind(lambda a: a / 2, lambda a: a + 6)(4), 8),
)


test_discretely = case_of(
    (lambda: tuple(discretely(lambda _: _)(print)), (print, )),
    (lambda: tuple(discretely(lambda _: _)(print |then>> sum)), (print, sum)),
    (
        lambda: (
            discretely(
                lambda action: lambda values: (*values, action(values[-1]))
            )(
                (lambda a: a + 1)
                |then>> (lambda b: b + 2)
                |then>> (lambda c: c + 3)
            )
        )([0]),
        (0, 1, 3, 6),
    ),
)


@mark.parametrize(
    'first_node, second_node, input_args',
    [
        (lambda x, y: x + y, lambda x: x ** x, (5, 3)),
        (lambda x: x**2 + 12, lambda x: x ** 4, (42, )),
        (lambda: 12, lambda x: x + 30, tuple())
    ]
)
def test_then_operator(
    first_node: Callable,
    second_node: Callable,
    input_args: Iterable
):
    assert (
        (first_node |then>> second_node)(*input_args)
        == ActionChain((first_node, second_node))(*input_args)
    )


def test_frm():
    result = (
        5 |frm| (lambda a: a + 10) |frm| (lambda a: a * 2) |frm| (lambda a: a + 10)
    )

    assert result == 40
