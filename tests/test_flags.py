from random import choice

from pyhandling.atoming import atomic
from pyhandling.flags import *
from pyhandling.testing import case_of


instance = flag_about("instance")
negative_instance = flag_about("negative_instance", negative=True)

first = flag_about("first")
second = flag_about("second")
third = flag_about("third")


def test_flag_algebra():
    assert first == first
    assert first != second
    assert nothing == nothing
    assert first != nothing

    assert first | second == first
    assert first | second == second
    assert first | nothing is first
    assert nothing | nothing is nothing

    assert tuple(first | second | third) == (first, second, third)
    assert len(first | second | third) == 3

    assert tuple(instance) == (instance, )
    assert len(instance) == 1

    assert tuple(nothing) == tuple()
    assert len(nothing) == 0

    assert pointed(4) | instance == pointed(4)

    assert pointed(1, 2, 3) == pointed(1) | pointed(2) | pointed(3)
    assert pointed(instance) is instance
    assert pointed() is nothing

    assert pointed(4).point == 4
    assert pointed(4).points == (4, )

    assert instance.point is instance
    assert instance.points == (instance, )

    assert nothing.point is nothing
    assert nothing.points == (nothing, )

    assert (first | second).point == first.point
    assert (first | second).points == (first.point, second.point)

    assert bool(instance) is True
    assert bool(negative_instance) is False

    assert bool(pointed(1)) is True
    assert bool(pointed(0)) is False

    assert bool(pointed(0) | instance) is True
    assert bool(pointed(0) | negative_instance) is False

    assert pointed(*range(11)).that(lambda n: n >= 7) == pointed(7, 8, 9, 10)
    assert pointed(*range(11)).that(lambda n: n >= 20) == nothing

    assert instance.that(lambda f: f == instance) == instance
    assert instance.that(lambda f: f == 0) == nothing

    assert atomic(pointed(1, 2, 3)).point == pointed(1).point

    assert pointed(1) != +pointed(1)
    assert pointed(1) != -pointed(1)

    assert (+pointed(3))(pointed(1, 2)).points == (1, 2, 3)
    assert (-pointed(3))(pointed(1, 2, 3)).points == (1, 2)
    assert (-pointed(1))(pointed(1)) is nothing

    assert ++pointed(1) == +pointed(1)
    assert --pointed(1) == +pointed(1)

    assert ~+pointed(1) == pointed(1)
    assert ~-pointed(1) is nothing

    assert (+pointed(2))(pointed(1)).points == (1, 2)

    assert (-pointed(2) ^ +pointed(3))(pointed(1, 2)).points == (1, 3)

    assert ~pointed(1) == pointed(1)


def test_flag_instance_check():
    flag_or_vector = choice([pointed(1), +pointed(1)])

    assert isinstance(~flag_or_vector, Flag)
    assert isinstance(+flag_or_vector, FlagVector)

    assert not isinstance(4, instance)
    assert isinstance(instance, instance)
    assert isinstance(instance, instance | negative_instance)
    assert not isinstance(instance, negative_instance)

    assert isinstance(1, pointed(int))
    assert isinstance(1, instance | int)
    assert isinstance(instance, instance | int)


test_to_points = case_of((
    lambda: to_points(lambda p: (p, 4))(instance | pointed(1, 2)).points,
    ((instance, 4), (1, 4), (1, 4)),
))


test_to_value_points = case_of((
    lambda: to_value_points(lambda p: p * 2)(instance | pointed(1, 2)).points,
    (instance, 2, 4),
))
