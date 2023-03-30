# Pyhandling
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

## Installation
`pip install pyhandling`

## Examples
### Execution flow
Connect actions in a chain

```py
from pyhandling import *


completed = str |then>> (lambda line: line + '6') |then>> int
completed(25)
```
```
256
```

with calling
```py
25 >= str |then>> (lambda line: line + '6') |then>> int
```
```
256
```

or via calling
```py
6 >= bind(lambda a: a + 10, lambda b: b / 2)
```
```
8.0
```

or via template
```py
4 >= binding_by(... |then>> (lambda b: b * 10) |then>> ...)(lambda x: x + 4)
```
```
84
```

or connect in width
```py
merged(lambda a: a - 1, lambda _: _, lambda c: c + 1)(2)
```
```
(1, 2, 3)
```

with result definition
```py
merged(print, lambda b: b + 1, return_from=1)(3)
merged(lambda a: a - 1, lambda _: _, lambda c: c + 1, return_from=slice(0, 3, 2))(2)
```
```
3
4
(1, 3)
```

merging the results
```py
mergely(
    lambda n: lambda a, d: a + str(n) + d,
    lambda n: str(n + 8),
    lambda n: str(n + 2),
)(2)
```
```
1024
```

Repeat calls
```py
repeating(lambda line: f"{line}{line[-1]}", times(3))("What?")
```
```
What????
```

Choose an action to call
```py
square_or_module_of = on(
    lambda number: number >= 0,
    lambda number: number ** 2,
    else_=abs,
)

square_or_module_of(4)
square_or_module_of(-4)
```
```
16
4
```

skipping input value
```py
incremented_or_not = on(lambda n: n % 2 == 0, lambda n: n + 1)

incremented_or_not(2)
incremented_or_not(3)
```
```
3
3
```

### Data flow
Ignore the output value
```py
with_result("Forced result", print)("Input value") + " and something"
```
```
Input value
Forced result and something
```

via arguments
```py
returnly(print)("Input argument") + " and something"
```
```
Input argument
Input argument and something
```

or ignore input arguments
```py
eventually(print, 16)('Some', 'any', "arguments")
```
```
16
```

to get something
```py
taken("Something")('Some', 'any', "arguments")
```
```
Something
```

or forced binary answer
```py
yes('Some', 'any', "arguments")
no('Some', 'any', "arguments")
```
```
True
False
```

Force unpack from argument
```py
with_positional_unpacking(print)(range(1, 4))
with_keyword_unpacking(lambda a, b: a + b)({'a': 5, 'b': 3})
```
```
1 2 3
8
```

from all sorts of arguments
```py
print_from = unpackly(print)

print_from(ArgumentPack(['Fish', "death"], {'sep': ' of '}))
print_from(ArgumentPack.of("Chair", "table", sep=' of '))
```
```
Fish of death
Chair of table
```

### Partial application
Add arguments by calling
```py
@fragmentarily
def sentence_from(first: str, definition: str, second: str, sign: str = '!') -> str:
    return f"{first} {definition} {second}{sign}"


sentence_from("A lemon")("is not", sign='.')("an orange")
```
```
A lemon is not an orange.
```

after input
```py
to_message_template = "{} {}{}".format

post_partial(to_message_template, "world", '!')("Hello")
```
```
Hello world!
```

under keyword
```py
with_keyword('n', 1, "{n}st {}".format)("day of spring")
```
```
1st day of spring
```

using pseudo-operators
```py
(to_message_template |to| "Hello")("world", '...')
(to_message_template |to* ("Hello", "world"))('?')

(to_message_template |by| '!')("Hello", "world")
```
```
Hello world...
Hello world?
Hello world!
```

or not necessarily now
```py
container = closed(to_message_template)
opened_container = container("Hello")

opened_container("container world", '!')
```
```
Hello container world!
```

using all possible ways
```py
post_container = closed(to_message_template, close=post_partial)

post_container('!')("Hello", "post container world")
```
```
Hello post container world!
```

### Atomic operations
Transform without transforms
```py
returned(256)
```
```
256
```

Use synonyms to raise an error
```py
raise_(Exception("Something is wrong"))
```
```
Traceback ...
Exception: Something is wrong
```

to transform a context manager's context
```py
to_context(lambda file: file.read())(open("file.txt"))
```

to transform in a context manager's context
```py
with_context_by(taken(imaginary_transaction), lambda number: number / 0)(64)
```
```
Traceback ...
ImaginaryTransactionError: division by zero
```

to use syntax constructions
```py
execute_operation(60, '+', 4) # 64
transform(False, 'not') # True

call(print, 1, 2, 3, sep=' or ') # 1 or 2 or 3
callmethod(dict(), 'get', None, "Default getting result") # Default getting result

data = dict()

setitem(data, "some-key", "some-value")
getitem(data, "some-key") # some-value
```

by creating them
```py
operation = operation_by('+', 4)
operation(60)
```
```
64
```

using syntax operators
```py
difference_between = operation_of('-')
difference_between(55, 39)
```
```
16
```

### Annotating
Use annotation templates to shorten annotations
```py
from pyhandling.annotations import *

from pyannotating import number


checker_of[number] # Callable[[int | float | complex], bool]

reformer_of[str] # Callable[[str], str]

handler_of[Exception] # Callable[[Exception], Any]

merger_of[str] # Callable[[str, str], str]

event_for[bool] # Callable[[], bool]

action_for[str] # Callable[[...], str]

formatter_of[object] # Callable[[object], str]

transformer_to[dict] # Callable[[Any], dict]
```

or annotations themselves
```py
atomic_action # Callable[[Any], Any]

checker # Callable[[Any], bool]

decorator # Callable[[Callable], Callable]

event # Callable[[], Any]
```

or comments integrated as annotations
```py
add_five_and_print: dirty[reformer_of[number]]
```

or prepared `TypeVars`
```py
from typing import Callable


devil_function: Callable[
    [
        Callable[[Callable[[*ArgumentsT], ValueT]], Callable[[ValueT], ResultT]],
        Callable[[ResultT], ActionT],
        Callable[[ErrorT], ErrorHandlingResultT],
        *ArgumentsT,
    ],
    ActionT | ErrorHandlingResultT
]
```

all of which can be viewed [here](https://github.com/TheArtur128/Pyhandling/blob/v3.0.0/pyhandling/annotations.py)


### Error handling
Handle errors that occur
```py
divide = rollbackable(operation_of('/'), returned)

divide(64, 4)
divide(8, 0)
```
```
16.0
division by zero
```

getting by unpacking
```py
divide = with_error(operation_of('/'))

result, error = divide(16, 0)


print(result, error, sep=', ')
```
```
nothing, division by zero
```

keeping error context
```py
ContextualError(
    ZeroDivisionError("division by zero"),
    dict(hero="Some hero", enemy="Some enemy"),
)
```
```
division by zero when {'hero': 'Some hero', 'enemy': 'Some enemy'}
```

nested way
```py
class DomainError(ContextualError):
    pass


class InfrastructureError(ContextualError):
    pass


root_error = InfrastructureError(
    DomainError(
        ZeroDivisionError("division by zero"),
        dict(hero="Some hero", enemy="Some enemy"),
    ),
    ["Some hero", "Some enemy", "Someone else"],
)

print(root_error)
```
```
division by zero when {'hero': 'Some hero', 'enemy': 'Some enemy'} when ['Some hero', 'Some enemy', 'Someone else']
```

with unpacking
```py
error, context = root_error

print(error, context, sep='\n')
```
```
division by zero when {'hero': 'Some hero', 'enemy': 'Some enemy'}
['Some hero', 'Some enemy', 'Someone else']
```

and getting them all
```py
print(*errors_from(root_error), sep='\n')
```
```
division by zero when {'hero': 'Some hero', 'enemy': 'Some enemy'} when ['Some hero', 'Some enemy', 'Someone else']
division by zero when {'hero': 'Some hero', 'enemy': 'Some enemy'}
division by zero
```

### Execution context
Break the chain of actions
```py
incremented_or_not: reformer_of[ContextRoot[number, Special[bad]]] = documenting_by(
    """
    Function to increase an input number if it is > 0.

    Takes as input a number wrapped in `ContextRoot`, using the `contextual`
    function or `ContextRoot(..., nothing)` directly and applies the nodes to
    its value inside an input `ContextRoot`.

    Executing in `maybe` context with the effect of saving a value computed
    before the returned `bad` flag.

    The value obtained in this way will have a `bad` context telling the
    contextual `maybe` execution to skip the given `root`.
    """
)(
    maybe(
        on(operation_by('<', 0), taken(bad))
        |then>> operation_by('**', 2)
        |then>> operation_by('*', 4)
    )
)


incremented_or_not(contextual(8))
incremented_or_not(contextual(-4))
```
```
256 when nothing
-4 when bad
```

in case of errors
```py
incremented: reformer_of[ContextRoot[number, Special[Exception]]]
incremented = until_error(
    operation_by('+', 10)
    |then>> operation_by('*', 2)
    |then>> (lambda number: number / (number - 28))
    |then>> operation_by('**', 2)
)


incremented(contextual(6))
incremented(contextual(4))
```
```
64.0 when nothing
28 when division by zero
```

and visualize results
```py
"result is {}".format(
    0 >= showly(
        operation_by('+', 1)
        |then>> operation_by('+', 2)
        |then>> operation_by('+', 3)
    )
)
```
```
1
3
6
result is 6
```

or interact with a context directly
```py
contextual(6) >= considering_context(
    operation_by('+', 4)
    |then>> contextual(in_collection |then>> taken, when=writing)
    |then>> operation_by('*', 6)
    |then>> operation_by('+', 4)
    |then>> contextual(
        closed(operation_of('/')) |then>> binding_by((getitem |by| 0) |then>> ...),
        when=reading,
    )
)
```
```
6.4 when (10,)
```

or don't interact
```py
contextual(1, when=bad) >= saving_context(
    operation_by('+', 2)
    |then>> operation_by('+', 3)
    |then>> operation_by('+', 4)
)
```
```
10 when bad
```

with the ability to get values
```py
root = incremented(contextual(4))

root.value
root.context
```
```
28
division by zero
```

using unpacking
```py
value, context = incremented_or_not(contextual(-16))

print(value, context, sep=', ')
```
```
-16, bad
```


Combine execution contexts
```py
incremented: reformer_of[ContextRoot[number, Special[bad | Exception]]]
incremented = documenting_by(
    """
    Function that increases a number using three compute contexts with one
    `ContextRoot`.
    """
)(
    maybe(
        operation_by('+', 4)
        |then>> on(operation_by('<=', 0), taken(bad))
        |then>> operation_by('*', 2)
    )
    |then>> until_error(
        operation_by('-', 14)
        |then>> (lambda n: n / (n - 2))
    )
    |then>> saving_context(
        operation_by('+', 0.25)
        |then>> operation_by('*', 4)
    )
)


incremented(contextual(-4))
incremented(contextual(4))
incremented(contextual(8))
```
```
4.5 when bad
9.0 when division by zero
6.0 when nothing
```

indicating special behavior
```py
incremented(contextual(8, when=bad))
```
```
4.0 when bad
```

Create an execution context
```py
from typing import Iterable


saving_results: mapping_to_chain_among[Iterable] = monadically(
    lambda node: lambda results: (*results, node(results[-1]))
)


(0, ) >= saving_results(
    operation_by('+', 1)
    |then>> operation_by('+', 2)
    |then>> operation_by('+', 3)
)
```
```
(0, 1, 3, 6)
```

limiting the effect of execution context
```py
"result is {}".format(
    4 >= showly(
        operation_by('*', 2)
        |then>> atomically(
            operation_by('-', 3)
            |then>> operation_by('*', 2)
        )
        |then>> atomically(
            operation_by('*', 10)
            |then>> str
        )
    )
)
```
```
8
10
100
result is 100
```

using a unique flag
```py
super_ = Flag("super")
not_super = Flag("not_super", sign=False)

not_super and super_ # not_super
isinstance(super_, super_ | not_super) # True

ContextRoot(16, super_) # 16 when super
```

representing context as a value
```py
context_oriented(contextual(4))
```
```
nothing when 4
```

or context types among themselves
```py
ContextRoot.like(ContextualError(
    ZeroDivisionError("division by zero"),
    dict(operand=4),
))

ContextualError.like(contextual(ZeroDivisionError("division by zero")))
```
```
division by zero when {'operand': 4}
division by zero when nothing
```

Annotate execution context
```py
mapping_to_chain_of[reformer_of[number]]
# Callable[
#     [Union[Callable[[Any], Any], Iterable[Callable[[Any], Any]]]],
#     ActionChain[Callable[[int | float | complex], int | float | complex]]
# ]

mapping_to_chain
# Callable[
#     [Union[Callable[[Any], Any], Iterable[Callable[[Any], Any]]]],
#     ActionChain[Callable[[Any], Any]]
# ]

mapping_to_chain_among[int]
# Callable[
#     [Union[Callable[[Any], Any], Iterable[Callable[[Any], Any]]]],
#     ActionChain[Callable[[int], int]]
# ]

execution_context_when[str]
# Callable[
#     [Union[Callable[[Any], Any], Iterable[Callable[[Any], Any]]]],
#     ActionChain[Callable[[ContextRoot[Any, str]], ContextRoot[Any, str]]]
# ]
```

### Batteries
Household functions
```py
showed(4) + 12
inversion_of(lambda: True)()
```
```
4
16
False
```

Collection non-generator functions
```py
map_(operation_by('**', 2), range(1, 11))
filter_(operation_by('>=', 5), range(1, 11))
zip_(range(10), 'abc')
```
```
(1, 4, 9, 16, 25, 36, 49, 64, 81, 100)
(5, 6, 7, 8, 9, 10)
((0, 'a'), (1, 'b'), (2, 'c'))
```

Collection functions
```py
with_opened_items([[1, 2, 3], 4, [5, 6]]) # (1, 2, 3, 4, 5, 6)

in_collection(4) # (4,)

as_collection(16) # (16,)
as_collection([1, 2, 3]) # (1, 2, 3)
```
```
```

```
```

Documentation decorator
```py
mega = documenting_by("""Flag indicating something.""")(
    Flag('mega')
)
```

Creating arbitrary objects
```py
with_attributes(name="Mohammed").__dict__
```
```
{'name': 'Mohammed'}
```

```
```
```




```
```

```
```
```



```
```
```

Immutable classes
```py
from typing import Iterable, Callable


@publicly_immutable
class CallingPublisher:
    name = DelegatingProperty('_name')
    followers = DelegatingProperty('_followers', getting_converter=tuple)

    def __init__(self, name: int, followers: Iterable[Callable] = tuple()):
        self._name = name
        self._followers = list(followers)

    def __repr__(self) -> str:
        return f"Publisher {self._name} with followers {self._followers}"

    def __call__(self, *args, **kwargs) -> None:
        for follower in self._followers:
            follower(*args, **kwargs)

    @to_clone
    def with_follower(self, follower: Callable) -> None:
        self._followers.append(follower)


original = CallingPublisher("Some publisher", [print])
```

that can't change any public attribute
```py
original.some_attr = "some value"
```
```
Traceback ...
AttributeError: Type CallingPublisher is immutable
```

and automatically clone without manual creation
```py
other = original.with_follower(operation_by('**', 4) |then>> print)

original.followers
other.followers
```
```
(<built-in function print>,)
(<built-in function print>, ActionChain(...))
```

what would eventually
```py
other(4)
```
```
4
256
```