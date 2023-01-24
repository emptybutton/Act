from typing import Callable, Any, Union, Iterable, Mapping, Sized

from pytest import mark

from pyhandling.checkers import Negationer, TypeChecker, LengthChecker


@mark.parametrize(
    'checker, resource',
    [
        (lambda resource: isinstance(resource, int), int()),
        (lambda resource: isinstance(resource, int), str()),
        (lambda number: number < 10, 3),
        (lambda number: number > 10, 3)
    ]
)
def test_negationer(checker: Callable[[Any], bool], resource: Any):
    assert not Negationer(checker)(resource) is checker(resource)


@mark.parametrize(
    'type_, resource',
    [
        (int, int()),
        (str, int()),
        (int | str, int()),
        (int | str, str()),
        (int | str, float()),
        (int | str | float | set | frozenset, range(0)),
        (Union[set, frozenset], set),
        (Union[set, frozenset], frozenset),
        (Union[set, frozenset, int, float, str, range, tuple], 1j),
        (Union[Iterable, int, str, Mapping], tuple()),
        (Union[Iterable, int, str, Mapping], 1j)
    ]
)
def test_type_checker(type_: type, resource: Any):
    assert TypeChecker(type_)(resource) == isinstance(resource, type_)


@mark.parametrize(
    "required_length, is_end_inclusive, collection, result",
    [
        (3, True, (None, ) * 2, True),
        (3, True, (None, ) * 3, True),
        (3, False, (None, ) * 3, False),
        (0, True, tuple(), True),
        (0, False, tuple(), False),
        ((5, 10), True, tuple(), False),
        ((5, 10), True, (None, ) * 5, True),
        ((5, 10), True, (None, ) * 10, True),
        ((5, 10), True, (None, ) * 7, True),
        ((5, 10), False, (None, ) * 10, False),
        ((5, 10, 12, 15), False, (None, ) * 5, True),
        ((5, 10, 12, 15), False, (None, ) * 11, True),
        ((5, 10, 12, 15), True, (None, ) * 15, True),
    ]
)
def test_length_checker(required_length: int, is_end_inclusive: bool, collection: Sized, result: bool):
    assert (
        LengthChecker(required_length, is_end_inclusive=is_end_inclusive)(collection)
        is result
    )