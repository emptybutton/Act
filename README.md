## Act
Library for advanced continuous handling of anything.

Provides tools to extend single call logic on a nearly unlimited scale.</br>
You can even integrate the entire program logic into one call.

### Installation
`pip install pyhandling`

### Overview
```py
from act import try_, v, w, to, catch, optionally, by, then, on, fmt


lookup = try_(v[w], to(catch(KeyError, to(None))))

# def lookup(table: Mapping[K, V], key: K) -> Optional[V]:
#    try:
#        return table[key]
#    except KeyError:
#        return None


main = optionally(
    (lookup |by| True)  # lambda table: lookup(table, True)
    |then>> on(v > 0, None)  # lambda v: None if v > 0 else v
    |then>> fmt("found {}", v + 1)  # lambda v: f"found {v + 1}" 
)


main(dict())  # None
main({True: 4})  # None
main({True: -4})  # found -3
```

### Features

> * [**Lambda generation**](#lambda-generation)
> * [**Pipeline**](#pipeline)
> * [**Partial application**](#partial-application)
> * [**Data flow**](#data-flow)
> * [**Syntax synonyms**](#syntax-synonyms)
> * [**Flags**](#flags)
> * [**Contextualization**](#contextualization)
> * [**Monads**](#monads)
> * [**Structural OOP**](#structural-oop)
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

...with currying
```py
main = a + b + c + d  # lambda a, b, c, d: a + b + c + d without curry >.<
main(1)()()(2, 3)()()(4)
```
```
10
```

...or attribute getting
```python
class WithA:
    def __init__(self, a):
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
main = _(v, *args, *kwargs.values_._())  # lambda v, *args, **kwargs: (v, *args, *kwargs.values())
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

</br>

> Item setting supports `tuple`.
> ```py
> main = t[1].set(8)
> main((1, 2, 3))
> ```
> ```
> (1, 8, 2)
> ```

</br>

...with side effects
```py
main = v.a.mset(w[1].mset(-x)).a

values = [1, 2, 3]
with_a = WithA(...)

main(with_a, values, 8)  # [1, -8, 3]
values  # [1, -8, 3]
with_a.a  # [1, -8, 3]
```

...and via a function
```py
main = v.a.mbe(lambda a: a * 4).a
with_a = WithA(64)

main(with_a)  # 256
with_a.a  # 256
```

</br>

> To use a function immutably use `be`.
> ```py
> main = t[1].be(lambda i: i**3)
> main((1, 2, 3))
> ```
> ```
> (1, 8, 2)
> ```

</br>


Use boolean logic operators
```py
v.and_(w)  # lambda v, w: v and w
v.or_(w)  # lambda v, w: v or w
v.is_(w)  # lambda v, w: v is w
v.is_not(w)  # lambda v, w: v is not w
v.in_(w)  # lambda v, w: v in w
v.not_in(w)  # lambda v, w: v not in w
v.has(w)  # lambda v, w: w in v
v.has_no(w)  # lambda v, w: w not in v
```

</br>

> Operators are executed in the order in which they are nested.
> ```py
> v.has(4).or_(w.has(4)).and_(False)  # always `False`
> ```

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
# lambda f: int |then>> f |then>> str |then>> (l + '!')

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
main = int |then>> str |then>> float |then>> int  # lambda v: int(float(str(int(v))))

tuple(main)  # (int, str, float, int)
len(main)  # 4
len(main * 2)  # 8

main[1]  # str
main[1:3]  # str |then>> float
```

...to decorate
```py
main = discretely(binding_by(... |then>> (v * 2)))

action = main(int |then>> str)  # int |then>> (v * 2) |then>> str |then>> (v * 2)
action(10.1)  # 2020

action = main(str)  # str |then>> (v * 2)
action(1)  # 11
```


</br>

> To remove secondary behavior of a pipeline or part of it, use `func`.
> ```py
> ...
> 
> action = main(int |then>> func(str |then>> (v + '48.')))
> # int |then>> (v * 2) |then>> func(str |then>> (v + '48.')) |then>> (v * 2)
> 
> action('10')
> ```
> ```
> 2048.2048.
> ```

> `bind` by default binds without secondary behavior.

> To generate a pipeline without secondary behavior from a template, use the `atomic_binding_by` shortcut.

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

> `TypeVar`s of one letter are already present in the library, so you do not need to create them.

</br>

### Data flow
Ignore arguments
```py
main = take[0][2, 3][5:7]['x'](_(*args, *kwargs.values_._()))
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
main = with_result("forced result", print)
main("argument") + " and something"
```
```
argument
forced result and something
```

...as an argument
```py
main = returnly(print)
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
main = once(shown)

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
main = via_indexer(v / w)
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

### Syntax synonyms
Use branching
```py
from typing import Any


on(v >= 0, v**2)  # lambda v: v**2 if v >= 0 else v
on(None, 4)  # lambda _: 4 if _ is None else _
on(None, 4, else_=0)  # lambda _: 4 if _ is None else 0


when(
    (n > 0, "positive"),
    (0, "zero"),
    (n < 0, "negative"),
    (..., "NaN: {}".format),
)

# def _(n: Any) -> str:
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
main = when(
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
times(3)(shown)  # lambda _: shown(shown(shown(_)))

while_(not_(None), v[0])

# def _(v) -> None:
#     while v is not None:
#         v = v[0]
#
#     return v
```

Raise errors
```py
raise_(Exception('o.O'))
```
```
Traceback ...
Exception: o.O
```

</br>

> Use the `raising` shortcut to ignore input arguments.
> ```py
> raising(Exception('o.O'))(...)
> ```
> ```
> Traceback ...
> Exception: o.O
> ```

</br>

Catch errors
```py
try_(1 / n, will("{} is undivided ({})".format))

# def _(n):
#     try:
#         return 1 / n
#     except Exception as error:
#         return f"{n} is undivided ({error})"
```

</br>

> To emulate an `except` block, use the `catch` function.
> ```py
> try_(
>     1 / n,
>     to(catch(ZeroDivisionError)(
>         print
>     )),
> )
> 
> # def _(n):
> #    try:
> #        return 1 / n
> #    except ZeroDivisionError as error:
> #        print(error)
> ```

</br>

Save errors
```py
main = with_error(v / w)

error, value = main(8, 2)  # (nothing, 4)
error, value = main(8, 0)  # (ZeroDivisionError('division by zero'), None)
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

Create discrete tests
```py
from unittest import main


test_something = case_of(
    (lambda: 5 + 3, 8),
    lambda: 4 in range(10),
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


> If there is no positive result, `True` is considered a positive result.

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

> `pointed` can annotate a value it declares.
> ```py
> pointed[int] == int | Flag[int]
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
> `&` operator and inverted back to flag by `~` operator.
> ```py
> ++pointed(1)  # +pointed(1)
> --pointed(1)  # +pointed(1)
> 
> ~+pointed(1) == pointed(1)
> ~-pointed(1) is nothing
> 
> (+pointed(2))(pointed(1))  # pointed(1, 2)
> 
> (-pointed(2) & +pointed(3))(pointed(1, 2))  # pointed(1, 3)
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

contextual(great, 4)
```
```
great 4
```

...nested
```py
...

very = flag_about("very")

contextual(very, great, 4)
```
```
very great 4
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

> To declare contextualization use the `be` function.
> ```py
> ...
> 
> be(great)(4)  # great 4
> be(great, great(4))  # great 4
> 
> nice = contextualizing(flag_about("nice"))
> 
> be(nice, great(4))  # nice great 4
> 
> be(+nice, great(4))  # great | nice 4
> be(+nice, 4)  # nice 4
> 
> be(-nice, nice(4))  # nothing 4
> be(-nice, 4)  # nothing 4
> ```

</br>

Get values
```py
...

context, value = great(4)

great(4).value == value == 4
great(4).context is context is great
```

</br>

> Note that with nested contextualization, data is structured recursively.
> ```py
> ...
> 
> very = contextualizing(flag_about("very"))
> 
> very(great(4))  # very great 4
> 
> very(great(4)).value  # great 4
> very(great(4)).context  # very
> ```

> To preserve some features of the described values, you can use other forms of contextualization

> For `Callable` objects:
> ```py
> safely = flag_about("safely")
> action_with_context = contextually(safely, print)
> 
> context, action = action_with_context
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
> some_error = Exception('o.O')
> error_with_context = ContextualError(from_domain, some_error)
> 
> context, error = error_with_context
> 
> error_with_context.error is error is some_error
> error_with_context.context is context is from_domain
> 
> raise error_with_context
> ```
> ```
> Traceback ...
> act.contexting.ContextualError: raisable(from_domain Exception('o.O'))
> ```

> Flag contextualization also supports all of these forms.
> ```py
> from_domain = contextualizing(flag_about("from_domain"), to=ContextualError)
> from_domain(Exception('o.O'))
> ```
> ```
> raisable(from_domain Exception('o.O'))
> ```

</br>


Declorate contextualization
```py
...

perfect = contextualizing(flag_about("perfect"))

contexted(4)  # nothing 4
contexted(perfect(4))  # perfect 4

contexted(4, perfect)  # perfect 4
contexted(great(4), perfect)  # perfect 4

contexted(great(4), +perfect)  # great | perfect 4
contexted(great(4), -great)  # nothing 4
```

</br>

> `contexted` can annotate a value it declares.
> ```py
> contexted[str]  # typing.Union[str, act.contexting.ContextualForm[typing.Any, str]]
> contexted[int, str]  # typing.Union[str, act.contexting.ContextualForm[int, str]]
> ```

</br>

...or a context
```py
with_context_that(v > 0, contextual(pointed(1, 2, 3), "mega"))  # 1 "mega"
with_context_that(v > 0, contextual(pointed(-1, -2, -3), "mega"))  # nothing "mega"
with_context_that(v > 0, "mega")  # nothing "mega"
```

Calculate value with a context
```py
nice = contextualizing(flag_about("nice"))

saving_context(v * 2)(nice(4))  # nice 8
saving_context(v * 2)(4)  # nothing 8

to_context(-nice)(nice(4))  # nothing 8
to_context(+nice)(4)  # nice 8

to_write(_(a, b))(nice(4))  # (nice, 4) 4
to_read(_(a, b))(nice(4))  # nice (nice, 4)
```

...with additional nesting
```py
...

to_metacontextual(+nice, v * 2)(contextual(contextual(4), nothing, 2))  # (nice 8) nice 4

is_metacontextual(nice(nice(8)))  # True

with_reduced_metacontext(contextual(2, 1, "mega"))  # 2 | 1 "mega"
with_reduced_metacontext(contextual(3, 2, 1, "mega"))  # 3 | 2 1 "mega"

with_reduced_metacontext(4)  # contextual(4)
with_reduced_metacontext(contextual(..., 4))  # contextual(..., 4)

without_metacontext(contextual(1, 2, 3, "mega"))  # 1 | 2 | 3 "mega"

metacontexted(contextual(1, 2, 3, "mega"))  # (1, 2, 3, 'mega')
metacontexted("mega")  # ('mega',)
```

</br>

> Similar to context initialization, contextualization form generics also work.
> ```py
> contextual[int]  # contextual[nothing, int]
> contextual[str, int]  # contextual[str, int]
> contextual[float, str, int]  # contextual[float, contextual[str, int]]
> ```

</br>


### Monads
Break execution on `None`
```py
main = optionally(
    (v - 10) |then>> {0: False, 1: True}.get |then>> fmt("<{}>", v)
)

main(10)  # <False>
main(16)  # None
```

...for calling
```py
optionally.call_by(5, 3)(v + w)  # 8
optionally.call_by(...)(None)  # None
optionally.call_by(None, 1)(v + w)  # None
```

...or not on `None`
```py
main = maybe(
    int
    |then>> on(v < 0, bad(ValueError("number must be greater than zero")))
    |then>> (v ** 2)
)

main(4)  # 16
main(-4)  # bad ValueError("number must be greater than zero")
```

...or on errors
```py
main = with_error(v / w) |then>> until_error((16 / v) |then>> "found {}!".format)

main(4, 0)  # ZeroDivisionError("division by zero") None
main(8, 2)  # nothing "found 4.0!"
main(0, 2)  # pointed(ZeroDivisionError("float division by zero")) 0.0
```

Write an output
```py
4 >= showly((v + 4) |then>> (v * 2) |then>> (v - 4))
```
```
8
16
12
```

...in different ways
```py
logs = list()

4 >= showly(show=logs.append)((v + 4) |then>> (v * 2) |then>> (v - 4))

logs  # [8, 16, 12]
```

Choose action by context
```py
main = either(
    (right, v + 1),
    (left, v - 1),
)

main(right(3))  # right 4
main(left(-3))  # left -4
main(0)  # nothing 0
```

</br>

> Otherwise, `either` is equivalent to `when`.

</br>


Defer execution
```py
main = in_future(shown |then>> float) |then>> saving_context(v ** 2)

print(main(4).value)
print(future(main(4)))
```
```
16
4
pointed(parallel 4.0) 16
```

Execute multilinearly
```py
main = do(print, v + 1, v ** 2)

main(4)
```
```
4
16
```

</br>

> `do` works with only one argument.

> `do` action is executed in the context of an empty arbitrary object that can be interacted.
> ```py
> do(up(shown) |then>> v * 2)(4)
> ```
> ```
> <> 4
> 8
> ```

> To write and read from context use `write` and `read` shortcuts.
> ```py
> do(
>     write(u.index.set(v * 2)),
>     read(u.index + v),
> )(10)
> ```
> ```
> 30
> ```

> To save the top context on return use `do.openly`.

> To set the default upping use `doing` and `doing(...).openly` respectively.

</br>


### Structural OOP
Create objects on the fly
```py
obj(name="William")  # <name="William">
obj(name="William").name  # William
```

...and modify 
```py
obj(name="William") & obj(age=24)  # <name="William", age=24>

(obj(name="William") & obj(age=24)) - 'age'  # <name="William">
obj(name="William") + 'age'  # <name="William", age=None>
```

</br>

> Objects are compared by value, support `instance` and create `Union` on `|` so
> ```py
> class WithA:
>     def __init__(a):
>         self.a = a
> 
> 
> obj(a=4) == WithA(4)
> 
> instance(obj(name="William"), obj(name="William"))
> not instance(obj(name="not William"), obj(name="William"))
> 
> instance(obj(name="William", age=24), obj(name="William"))
> not instance(obj(name="William"), obj(name="William", age=24))
> 
> instance(obj(name="William"), obj(name="William") | obj(age=24))
> instance(obj(age=24), obj(name="William") | obj(age=24))
> ```

</br>

Use methods
```py
namespace = obj(a=2, main=as_method(lambda self, b: self.a ** b))

namespace.main  # <bound method <lambda> of <a=2, main=callable(as_method <lambda>)>>
namespace.main(4)  # 16
```

...properties
```py
container = obj(_value=0, value=as_property(v._value, v._value.mset(w * 4)))
# container = obj(_value=0, value=as_property(property(v._value, v._value.mset(w * 4))))

container.value  # 0
container.value = 16  # 64
```

...and descriptors in general
```py
obj(value=as_descriptor(obj(__get__=to(256)))).value
```
```
256
```

Use callable objects
```py
obj(__call__=print)(1, 2, 3, sep=' -> ')
obj(__call__=as_method(print))(1, 2, 3, sep=' -> ')
```
```
1 -> 2 -> 3
<__call__=callable(as_method print)> -> 1 -> 2 -> 3
```

Create from others
```py
class Alpha:
    a = 1


class Beta:
    def __init__(self, b):
        self.b = b


obj.of(Alpha, Beta(2))
```
```
<__module__="__main__", a=1, __doc__=None, b=2>
```


Create object templates
```py
User = temp(name=str, age=int)  # <name: str, age: int>

User("Oliver", 24)  # <name="Oliver", age=24>
```
```

```

</br>

> Behaviorally, templates are equivalent to objects.
> ```py
> temp(name=str) & temp(age=int)  # <name: str, age: int>
> 
> User = temp(name=str) & obj(age=24)  # <name: str, age=24>
> User("Oliver")  # <name="Oliver", age=24>
> 
> (temp(name=str) & temp(age=int)) - 'age'  # <name: str>
> temp(name=str) + 'age'  # <name: str, age=None>
> 
> (temp(name=str) & obj(__call__=print))("Oliver")(1, 2, 3, sep=' -> ')  # 1 -> 2 -> 3
> 
> temp() == obj()
> 
> isinstance(obj(name="Oliver", age=24), temp(name=str))
> isinstance(obj(name="Oliver", age=24), temp(name=str) & obj(age=24))
> not isinstance(obj(name="Oliver", age=24), temp(name=str) & obj(age=26))
> 
> isinstance(obj(name="Oliver"), temp(name=str) | temp(age=int))
> isinstance(obj(age=24), temp(name=str) | temp(age=int))
> 
> combination = (temp(name=str) & obj(age=24)) | (obj(name="Oliver") & temp(age=int))
> 
> isinstance(obj(name="Stone", age=24), combination)
> not isinstance(obj(name="Stone", age=22), combination)
> isinstance(obj(name="Oliver", age=2023), combination)
> ```

> `temp.of` works like `obj.of` with `temp` constructor but with additional behavior for dataclasses.
> ```py
> from dataclasses import dataclass, field
> 
> 
> @temp.of
> @dataclass
> class Struct:  # <a: int, b=2, c=4>
>     a: int
>     b: int = 2
>     c: int = field(default_factory=lambda: 4)
> ```

</br>

Use duck typing
```py
@dataclass
class User:
    name: str
    age: int


isinstance(obj(name="Oliver", age=24), Proto[User])
isinstance(obj(name="Oliver", age=24, is_mvp=True), Proto[User])
not isinstance(obj(name="Oliver"), Proto[User])
```

Create proxies
```py
original = obj(a=1)

sculpture = sculpture_of(original, number='a')

sculpture.number = 16
sculpture.number == original.a == 16
```

...dynamically
```py
...

proxy_of = sculpture_of(number=o.a / 2, value=property(v.a, v.a.mset(w * 2)))

sculpture = proxy_of(original)

sculpture.number == 8
sculpture.value == 16

sculpture.number = 4  # AttributeError: property of 'obj' object has no setter
sculpture.value = 4

original.a == 8
```

</br>

> To get an original object to which a sculpture delegates use `original_of`.
> ```py
> ...
> 
> original_of(sculpture) is original
> ```

</br>

Declare a read-only getting
```py
class Container:
    value: int = 4

    a: read_only[int] = read_only("value")
    b: read_only[int] = read_only(property(v.value, v.value.mset(w)))


container = Container()

container.a == container.b == container.value == 4

container.a = ...  # AttributeError: attribute cannot be set
container.b = ...  # AttributeError: attribute cannot be set
```

</br>

> `read_only` can be used as an annotation.

</br>

Transfer data
```py
class WithA:
    def __init__(self, a):
        self.a = a


with_a = WithA(None)

from_(obj(a=1, b=2), with_a)

type(with_a)  # <class '__main__.WithA'>
with_a.__dict__  # {'a': 1, 'b': 2}
```

Use optional attributes
```py
out(obj(a=4)).a == 4
out(obj()).a is None

original = obj(a=4)

out(original).a = 8
out(original).b = 8

original  # <a=8>
```
