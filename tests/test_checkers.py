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


