## Act
Library for advanced continuous handling of anything.

Provides tools to extend single call logic on a nearly unlimited scale.</br>
You can even integrate the entire program logic into one call.

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


main(dict())  # nothing None
main({True: 4})  # nothing "found 5"
main({True: -4})  # bad -4
```

### Features

> * [**Lambda generation**](#lambda-generation)
> * [**Pipeline**](#pipeline)
> * [**Partial application**](#partial-application)
> * [**Data flow**](#data-flow)
> * [**Function generation**](#function-generation)
> * [**Test generation**](#test-generation)
> * [**Flags**](#flags)
> * [**Contextualization**](#contextualization)
> * [**Monads**](#monads)
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
> The order in which arguments are assigned to cursors corresponds to the alphabetical number of the letter of which the cursor is named.

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
> </br>E.g. `v.__` or `v.values_`.

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
main = _.(v, *args, *kwargs.values_._())  # lambda v, *args, **kwargs: (v, *args, *kwargs.values())
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

### Pipeline
Combine calls together
```py
main = int |then>> (v + 6) |then>> str |then>> (l + '!')  # lambda v: str(int(v) + 4) + '!'
main(10)
```
```
16!
```

</br>

> Cursors cannot generate pipeline.

</br>

Execute Instantly
```py
10 >= (v * 2) |then>> str |then>> (l + '23')  # (lambda v: str(v * 2) + '23')(10)
```
```
2023
```

Insert functions into templates
```py
main = binding_by(int |then>> ... |then>> str |then>> (l + '!'))

func = main(v + 3)  # int |then>> (v + 3) |then>> str |then>> (l + '!')
func('5')
```
```
8!
```

</br>

> Places for insertion are not limited.

</br>

Create a pipeline from collections
```py
main = ActionChain([int, v**2, str, l + " >= 0"])  # int |then>> (v**2) |then>> str |then>> (l + " >= 0")
main(4)
```
```
16 >= 0
```

...or in higher order functions
```py
from functools import reduce


main = reduce(bind, [int, v**2, str, l + " >= 0"])  # int |then>> (v**2) |then>> str |then>> (l + " >= 0")
main(-4)
```
```
16 >= 0
```

Interact with a pipeline in the same way as with a regular collection
```py
main = int |then>> str |then>> float |then>> int

main[1] is str
main[1:3] == str |then>> float

len(main) == 4

tuple(main) == (int, str, float, int)
```

...to decorate
```py
main = discretely(binding_by(... |then>> (v * 2)))  # there is no such >.<

func = main(int |then>> str)  # int |then>> (v * 2) |then>> str |then>> (v * 2)
func(10.1)  # 2020

func = main(str)  # str |then>> (v * 2)
func(1)  # 11
```


</br>

> To remove secondary behavior of a pipeline or part of it, use `atomically`.
> ```py
> ...
> 
> # int |then>> (v * 2) |then>> atomically(str |then>> (v + '48.')) |then>> (v * 2)
> func = main(int |then>> atomically(str |then>> (v + '48.')))
> 
> func('10')
> ```
> ```
> 2048.2048.
> ```

> `bind` by default binds without secondary behavior.

> To generate a fully atomic pipeline from a template, use the `atomic_binding_by` shortcut.

</br>


### Partial application
Memorize arguments
```py
from operator import truediv


divide_8_by = partial(truediv, 8)  # lambda _: truediv(8, _)
divide_by_2 = rpartial(truediv, 2)  # lambda _: truediv(_, 2)

divide_8_by(2)  # 4
divide_by_2(8)  # 4
```

</br>

> `act` uses its implementation of `partial`.

</br>

...using call
```py
from operator import truediv


divide_8_by = will(truediv)(8)  # (lambda a: lambda b: truediv(a, b))(8)
divide_by_2 = rwill(truediv)(2)  # (lambda b: lambda a: truediv(a, b))(2)

divide_8_by(2)  # 4
divide_by_2(8)  # 4
```

...or pseudo-operators
```py
(truediv |to| 8)(2)  # 4
(truediv |by| 2)(8)  # 4
```

...with unpacking
```py
args = (1, 2, 3)

(print |to* args)(4)  # 1 2 3 4
(print |by* args)(0)  # 0 1 2 3
```

</br>

> Pseudo-operators is preferred over `partial` and `rpartial` functions for one argument.

</br>

Add automatic partial application
```py
@partially
def func(a: A, b: B, c: C, *, d: D = 4) -> tuple[A, B, C, D]:
    return (a, b, c, d)


func(1, 2, 3)  # (1, 2, 3, 4)
func(1)(2)(3)  # (1, 2, 3, 4)
func(1, 2)(3)  # (1, 2, 3, 4)
func(0, 1, d=3)(2)  # (0, 1, 2, 3)
```

</br>

> `TypeVar`s of one letter are already present in the library, so you do not need to create them

</br>

### Data flow
Ignore arguments
```py
main = take[0][2, 3][5:7]['x'](_(*args, *kwargs.values_._()))  # there is no such >.<
main(*range(10), a='a', b='b', x='x')
```
```
(0, 2, 3, 5, 6, x)
```

...all
```py
main = eventually(print, 42)  # lambda *_, **__: print(42)
main(*range(100), a='a', b='b', c='c', d='d')
```
```
42
```

...to get something
```py
to("something")(...)  # (lambda *_, **__: "something")(...)
```
```
something
```

</br>

> To get `True` or `False` in this way you can use `yes` and `no` shortcuts.

</br>

Execute with prepared result
```py
main = with_result("forced result", print)  # there is no such >.<
main("argument") + " and something"
```
```
argument
forced result and something
```

...as an argument
```py
main = returnly(print)  # there is no such >.<
main("argument") + " and something"
```
```
argument
argument and something
```

</br>

> To print with return just like in that example, you can use the `shown` shortcut.

</br>

Flip parameters
```py
from operator import truediv


flipped(truediv)(10, 1)
```
```
0.1
```

Execute only once
```py
main = once(shown)  # there is no such >.<

main("value") + " and something"
main("value") + " and something"
```
```
value
value and something
value and something
```

Execute via indexer
```py
main = via_indexer(v / w)  # there is no such >.<
main[16, 2]
```
```
8
```

...or with indexer
```py
@and_via_indexer(t | float)
def main(v: int | float) -> int | float:
    return v + 3


main(5)  # 8
main[int]  # int | float
```

Compare positively
```py
anything == ...  # True
```

### Function generation
Use branching
```py
on(v >= 0, v**2)  # lambda v: v**2 if v >= 0 else v
on(None, 4)  # lambda _: 4 if _ is None else None
on(None, 1, else_=0)  # lambda _: 1 if _ is None else 0


matching(
    (n > 0, "positive"),
    (0, "zero"),
    (n < 0, "negative"),
    (..., "NaN: {}".format),
)

# def _(n: int | float) -> str:
#     if n > 0:
#         return "positive"
#     elif n == 0:
#         return "zero"
#     elif n < 0:
#         return "negative"
#     else:
#         return f"NaN: {n}"
```

...with stopping
```py
main = matching(  # there is no such >.<
    (n > 0, "positive"),
    (0, break_),
    (n <= 0, "negative"),
    (..., 'NaN'),
)

main(4)  # positive
main(0)  # NaN
main(-4)  # negative
main(list()) # NaN
```

Use decorating predicates
```py
not_(isinstance |by| int)  # lambda _: not isinstance(_, int)

bool(not_(None))  # True
not_(None)(...)  # True
not_(None)(None)  # False


and_(n >= 0, 1, isinstance |by| int)  # lambda n: n >= 0 and n == 1 and isinstance(n, int)

bool(and_(True, True))  # True
bool(and_(True, False))  # False


or_(None, 0, isinstance |by| bool)  # lambda _: _ is None or _ == 0 or isinstance(_, bool)

bool(or_(True, False, False))  # True
bool(or_(False, False, False))  # False
```

Use formatting
```py
main = fmt("({}) -> ({second})", int | t, second=int | t)  # lambda t: f"({int | t}) -> ({int | t})"
main(float)
```
```
(int | float) -> (int | float)
```

</br>

> Each function in `fmt` is executed with all arguments

</br>

Use cycles
```py
repeating(shown, times(3))  # lambda _: shown(shown(shown(_)))

repeating(v[0], while_=not_(None))

# def _(v) -> None:
#     while v is not None:
#         v = v[0]
#
#     return v
```

Raise errors
```py
raise_(Exception('>.<'))
```
```
Traceback ...
Exception: >.<
```

Catch errors
```py
trying_to(1 / n, will("{} is undivided ({})".format))

# def _(n):
#     try:
#         return 1 / n
#     except Exception as error:
#         return f"{n} is undivided ({error})"
```

Use context manager
```py
text = with_(open("file.txt"), f.read._())

# with open("file.txt") as f:
#     text = f.read()
```

Assert something
```py
assert_(False)
```
```
Traceback ...
AssertionError
```

### Test generation
Create discrete tests
```py
from unittest import main


def get_db() -> ...:
    ...


test_something = case_of(
    (lambda: 5 + 3, 8),
    lambda: get_db,
)


if __name__ == "__main__":
    main()
```
```
..
----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK
```


</br>

> Cases consist of a body (the first element of the tuple) and a positive result of the body (the second). </br>
> The body is a function that is called without arguments.


> In the absence of a positive result, any result is considered positive.

### Flags
Create objects that display something
```py
alpha = flag_about("alpha")
beta = flag_about("beta")
gamma = flag_about("gamma")
```

</br>

> Flags are combined with the `|` operator and subtracted with `-`.</br>
> Presence check is done with `==` operator.

> Flags are combined by `or` nature so
> ```py
> alpha | beta == alpha
> alpha | beta == beta
> alpha | beta == alpha | beta
> alpha | beta == alpha | gamma
> alpha | beta is not alpha
> ```

> Subtracts optional so
> ```py
> alpha - beta is alpha
> (alpha | beta) - beta is alpha
> ```

> There is a specific `nothing` flag that is a neutral element so
> ```py
> alpha | nothing is alpha
> alpha | nothing != nothing
> 
> alpha - alpha is nothing
> 
> nothing == nothing
> nothing | nothing is nothing
> ```

> Flags are iterable by its sum so
> ```py
> tuple(alpha | beta | gamma) == (alpha, beta, gamma)
> len(alpha | beta | gamma) == 3
> 
> tuple(alpha) == (alpha, )
> len(alpha) == 1
> 
> tuple(nothing) == tuple()
> len(nothing) == 0
> ```

> Flags indicate something.</br>
> It can be any value or abstract phenomenon expressed only by this flag.

> Flags indicating a value can be obtained via the `pointed` function.
> ```py
> pointed(4) | alpha == pointed(4)
> 
> pointed(1, 2, 3) == pointed(1) | pointed(2) | pointed(3)
> pointed(alpha) is alpha
> pointed() is nothing
> 
> pointed(4).point == 4
> pointed(4).points == (4, )
> 
> nothing.point is nothing
> nothing.points == tuple()
> 
> (alpha | beta).point == alpha.point
> (alpha | beta).points == (alpha.point, beta.point)
> ```

> Flags indicating a value are binary by value.</br>
> Nominal by their signs.
> ```py
> terrible = flag_about("terrible", negative=True)
> 
> bool(alpha) is True
> bool(terrible) is False
> 
> bool(pointed(1)) is True
> bool(pointed(0)) is False
> 
> bool(pointed(0) | alpha) is True
> bool(pointed(0) | terrible) is False
> ```

> Flags can be selected by their `point` using the `that` method.
> ```py
> pointed(*range(11)).that(n >= 7) == pointed(7, 8, 9, 10)
> pointed(*range(11)).that(n >= 20) == nothing
> 
> alpha.that(f == alpha) == alpha
> alpha.that(f == 0) == nothing
> ```

> Flag sums can be represented in atomic form.
> In this case, the atomic version is technically a representation of all flags of the sum,
> and at the same time none, in one flag, but in fact, it is just a first selected flag.
> ```py
> atomic(pointed(1, 2, 3))  # pointed(1)
> ```

> Don't use the atomic form to get exactly a first flag.
> The flag sum does not guarantee the preservation of the sequence (although it still implements it).

> Flags can be represented in vector form via unary plus or minus and added via call.
> ```py
> pointed(1) != +pointed(1)
> pointed(1) != -pointed(1)
> 
> (+pointed(3))(pointed(1, 2))  # pointed(1, 2, 3)
> (-pointed(3))(pointed(1, 2, 3))  # pointed(1, 2)
> (-pointed(1))(pointed(1))  # nothing
> ```

> Flag vectors have unary plus and minus and a sum, which can be created with the
> `^` operator and inverted back to flag by `~` operator.
> ```py
> ++pointed(1)  # +pointed(1)
> --pointed(1)  # +pointed(1)
> 
> ~+pointed(1) == pointed(1)
> ~-pointed(1) is nothing
> 
> (+pointed(2))(pointed(1))  # pointed(1, 2)
> 
> (-pointed(2) ^ +pointed(3))(pointed(1, 2))  # pointed(1, 3)
> ```

> Flags also use `~` to come to themselves, which can be used with a `Union`
> type with a vector to cast to Flag.
> ```py
> from random import choice
> 
> 
> ~pointed(1) == pointed(1)
> 
> flag_or_vector = choice([pointed(1), +pointed(1)])
> 
> isinstance(~flag_or_vector, Flag) is True  # always
> isinstance(+flag_or_vector, FlagVector) is True  # always
> ```

> Flags available for instance checking as a synonym for `instance` checking
> by `points`.
> ```py
> isinstance(4, alpha) is False
> isinstance(alpha, alpha) is True
> isinstance(alpha, alpha | terrible) is True
> isinstance(alpha, terrible) is False
> 
> isinstance(1, pointed(int)) is True
> isinstance(1, alpha | int) is True
> isinstance(alpha, alpha | int) is True
> ```

</br>

Create callable flags
```py
alpha = flag_about("alpha").to(v**2).to(-v)  # flag_about("alpha").to((v**2) |then>> (-v))
alpha(4)
```
```
-16
```

</br>

> Only named flags can be callable.

</br>


### Contextualization
Add a second value to one value, which in one form or another will describe the first value
```py
great = flag_about("great")

contextual(4, great)
```
```
great 4
```

</br>

> If you describe by a flag you can make it callable on that contextualization
> ```py
> great = contextualizing(flag_about("great"))
> great(4)
> ```
> ```
> great 4
> ```

</br>

Get values
```py
value, context = great(4)

great(4).value == value == 4
great(4).context is context is great
```

</br>

> To preserve some features of the described values, you can use other forms of contextualization

> For `Callable` objects:
> ```py
> safely = flag_about("safely")
> action_with_context = contextually(print, safely)
> 
> action, context = action_with_context
> 
> action_with_context.action is action is print
> action_with_context.context is context is safely
> 
> action_with_context(1, 2, 3, sep=" -> ")
> ```
> ```
> 1 -> 2 -> 3
> ```

> For `Exception`s:
> ```py
> from_domain = flag_about("from_domain")
> 
> some_error = Exception('>.<')
> error_with_context = ContextualError(some_error, from_domain)
> 
> error, context = error_with_context
> 
> error_with_context.error is error is some_error
> error_with_context.context is context is from_domain
> 
> raise error_with_context
> ```
> ```
> Traceback ...
> act.contexting.ContextualError: ContextualError(from_domain Exception('>.<'))
> ```

> Flag contextualization also supports all of these forms
> ```py
> from_domain = contextualizing(flag_about("from_domain"), to=ContextualError)
> from_domain(Exception('>.<'))
> ```
> ```
> ContextualError(from_domain Exception('>.<'))
> ```

</br>