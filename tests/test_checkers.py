from typing import Callable, Union, Iterable, Mapping, Sized

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
def test_negationer(checker: Callable[[any], bool], resource: any):
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
def test_type_checker(type_: type, resource: any):
    assert TypeChecker(type_)(resource) == isinstance(resource, type_)


