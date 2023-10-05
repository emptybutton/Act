from act.contexting import contextual
from act.cursor_base import (
    _ActionCursor, _ActionCursorNature, _ActionCursorParameter,
    _ActionCursorParameterUnionType
)
from act.partiality import partial


__all__ = (
    "same",
    "act",
    '_',
    'a',
    'b',
    'c',
    'd',
    'e',
    'f',
    'g',
    'h',
    'i',
    'j',
    'k',
    'l',
    'm',
    'n',
    'o',
    'p',
    'q',
    'r',
    's',
    't',
    'u',
    'v',
    'w',
    'x',
    'y',
    'z',
    "args",
    "kwargs",
)


same = partial(_ActionCursor._lift, is_static=False)


act = _ActionCursor(nature=contextual(_ActionCursorNature.external))
_ = _ActionCursor(nature=contextual(_ActionCursorNature.external))

a = _ActionCursor._operated_by(_ActionCursorParameter('a', 27))
b = _ActionCursor._operated_by(_ActionCursorParameter('b', 26))
c = _ActionCursor._operated_by(_ActionCursorParameter('c', 25))
d = _ActionCursor._operated_by(_ActionCursorParameter('d', 24))
e = _ActionCursor._operated_by(_ActionCursorParameter('e', 23))
f = _ActionCursor._operated_by(_ActionCursorParameter('f', 22))
g = _ActionCursor._operated_by(_ActionCursorParameter('g', 21))
h = _ActionCursor._operated_by(_ActionCursorParameter('h', 20))
i = _ActionCursor._operated_by(_ActionCursorParameter('i', 19))
j = _ActionCursor._operated_by(_ActionCursorParameter('j', 18))
k = _ActionCursor._operated_by(_ActionCursorParameter('k', 17))
l = _ActionCursor._operated_by(_ActionCursorParameter('l', 16))
m = _ActionCursor._operated_by(_ActionCursorParameter('m', 15))
n = _ActionCursor._operated_by(_ActionCursorParameter('n', 14))
o = _ActionCursor._operated_by(_ActionCursorParameter('o', 13))
p = _ActionCursor._operated_by(_ActionCursorParameter('p', 12))
q = _ActionCursor._operated_by(_ActionCursorParameter('q', 11))
r = _ActionCursor._operated_by(_ActionCursorParameter('r', 10))
s = _ActionCursor._operated_by(_ActionCursorParameter('s', 9))
t = _ActionCursor._operated_by(_ActionCursorParameter('t', 8))
u = _ActionCursor._operated_by(_ActionCursorParameter('u', 7))
v = _ActionCursor._operated_by(_ActionCursorParameter('v', 6))
w = _ActionCursor._operated_by(_ActionCursorParameter('w', 5))
x = _ActionCursor._operated_by(_ActionCursorParameter('x', 4))
y = _ActionCursor._operated_by(_ActionCursorParameter('y', 3))
z = _ActionCursor._operated_by(_ActionCursorParameter('z', 2))

args = _ActionCursor._operated_by(_ActionCursorParameter(
    "args",
    1,
    union_type=_ActionCursorParameterUnionType.POSITIONAL,
))

kwargs = _ActionCursor._operated_by(_ActionCursorParameter(
    "kwargs",
    0,
    union_type=_ActionCursorParameterUnionType.KEYWORD,
))
