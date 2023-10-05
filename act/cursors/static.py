from act.cursors.dynamic import *
from act.cursor_base import _static, _ActionCursor
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


same = partial(_ActionCursor._lift, is_static=True)


act = _static(act)
_ = _static(_)

a = _static(a)
b = _static(b)
c = _static(c)
d = _static(d)
e = _static(e)
f = _static(f)
g = _static(g)
h = _static(h)
i = _static(i)
j = _static(j)
k = _static(k)
l = _static(l)
m = _static(m)
n = _static(n)
o = _static(o)
p = _static(p)
q = _static(q)
r = _static(r)
s = _static(s)
t = _static(t)
u = _static(u)
v = _static(v)
w = _static(w)
x = _static(x)
y = _static(y)
z = _static(z)

args = _static(args)
kwargs = _static(kwargs)
