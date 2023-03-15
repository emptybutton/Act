from pyhandling.binders import post_partial, mirror_partial, close, unpackly
from pyhandling.tools import ArgumentPack


def sum_of(first, second, third=3, fourth=4):
    """Stub function for testing currying."""

    return first + second + third + fourth


def test_post_partial():
    assert post_partial(sum_of, 2)(1) == sum_of(1, 2)


def test_mirror_partial():
    assert (
        mirror_partial(sum_of, (2, ), (1, ))(third=tuple(), fourth=tuple())
        == sum_of((1, ), (2, ), tuple(), tuple())
    )


def test_default_close():
    assert close(sum_of)(1)(2) == sum_of(1, 2)




def test_unpackly_via_argument_pack():
    assert (
        unpackly(sum_of)(ArgumentPack.of(2, 4, third=6, fourth=8))
        == sum_of(2, 4, third=6, fourth=8)
    )