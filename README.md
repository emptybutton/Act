## Act
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

### Installation
`pip install pyhandling`

### Overview
```py
from act import trying_to, v, w, to, catching, maybe, by, then, on, bad, fmt


lookup = trying_to(v[w], to(catching(KeyError, to(None))))

# def lookup(table: Mapping[K, V], key: K) -> Optional[V]:
#    try:
#        return table[key]
#    except KeyError:
#        return None


main = maybe(
    (lookup |by| True)  # lambda table: lookup(table, True)
    |then>> on(v < 0, bad)  # lambda v: bad(v) if v < 0 else v
    |then>> fmt("found {}", v + 1)  # lambda v: f"found {v + 1}" 
)


main(dict())  # None when nothing
main({True: 4})  # found 5 when nothing
main({True: -4})  # -4 when bad
```

### Features

> * [**Lambda generation**](#lambda-generation)
> * [**Composition**](#composition)
> * [**Currying**](#currying)
> * [**Data flow**](#data-flow)
> * [**Function generation**](#function-generation)
> * [**Test generation**](#test-generation)
> * [**Monads**](#monads)
> * [**Flags**](#flags)
> * [**Immutability**](#immutability)
> * [**Arbitrary OOP**](#arbitrary-oop)
> * [**Error management**](#error-management)
> * [**Structure tools**](#structure-tools)

### Lambda generation
Use all functionality of lambda functions without **LAMBDA**
```py
main = a + b  # lambda a, b: a + b
main(10, 6)
```
```
16
```
</br>

> Lambdas are generated using single-letter cursors. Each individual letter represents one argument. </br>
The order in which arguments are assigned to cursors corresponds to the alphabetical number of </br>
the letter of which the cursor is named.

</br>

With currying
```py
main = a + b + c + d  # lambda a, b, c, d: a + b + c + d without curry >.<
main(1)()()(2, 3)()()(4)
```
```
10
```

...or attribute getting
```python
from typing import Any


class WithA:
    def __init__(self, a: Any):
        self.a = a


main = v.a + w*x  # lambda v, w, x: v.a + w*x
main(WithA(10), 3, 2)
```
```
16
```

To generate a call, use the `_` cursor method
```py
main = v.lowwer._() + w._(x + '?')  # lambda v, w, x: v.lowwer() + w(x + '?')
main('ABC', lambda x: x * 3, '!')
```
```
abc!?!?!?
```

</br>

> To interact with names that cursors have, just add underscore to them.
> </br>E.g. `v.__` or `v.keys_`.

</br>

Use `_` cursor to interact from outside
```py
main = _.len(_[v - w, v + w, _(v, v)])  # lambda v, w: len([v - w, v + w, (v, v)])
main(10, 5)
```
```
3
```

</br>

> If you can't use the `_` cursor use the `act` equivalent cursor.
> </br> E.g. `act(v, w)` instead of `_(v, w)`.


> An external cursor that generates a get from a variable cannot be called and, if attempted, generates a call.

</br>

Use unlimited arguments
```py
main = _.(v, *args, *kwargs.values._())  # lambda v, *args, **kwargs: (v, *args, *kwargs.values())
main(1, 2, a=3, b=4)
```
```
(1, 2, 3, 4)
```

Set attributes or items
```py
main = v.a.set(w[1].set(-x)).a  # there is no such >.<
main(WithA(...), [1, 2, 3], 8)
```
```
[1, -8, 3]
```

...with side effects
```py
main = v.a.set(w[1].set(-x, mutably=True), mutably=True).a  # there is no such >.<

values = [1, 2, 3]
with_a = WithA(...)

main(with_a, values, 8)  # [1, -8, 3]
with_a.a  # [1, -8, 3]
values  # [1, -8, 3]
```

...and via a function
```py
main = v.a.as_(lambda a: a * 4, mutably=True).a  # there is no such >.<
with_a = WithA(64)

main(with_a)  # 256
with_a.a  # 256
```

Use boolean logic operators
```py
v.and_(w)  # lambda v, w: v and w
v.or_(w)  # lambda v, w: v or w
v.is_(w)  # lambda v, w: v is w
v.is_not(w)  # lambda v, w: v is not w
v.in_(w)  # lambda v, w: v in w
v.not_in(w)  # lambda v, w: v not in w
v.contains(w)  # lambda v, w: w in v
v.contains_no(w)  # lambda v, w: w not in v
```

</br>

> Operators are executed in the order in which they are nested and such a function will always return `False`:
> </br> `v.contains(4).or_(w.contains(4)).and_(False)`
