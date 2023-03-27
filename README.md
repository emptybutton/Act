# Pyhandling
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

## Installation
`pip install pyhandling`

## Examples
### Execution flow
Connect functions in a chain

```python
from pyhandling import *


complete = str |then>> (lambda line: line + '6') |then>> int
complete(25)
```
```
256
```

with calling
```python
25 >= str |then>> (lambda line: line + '6') |then>> int
```
```
256
```

or via calling
```python
6 >= bind(lambda a: a + 10, lambda b: b / 2)
```
```
8
```

or via template
```python
4 >= binding_by(... |then>> (lambda a: a * 10) |then>> ...)(lambda number: number + 4)
```
```
84
```

or connect in width
```python
merged(lambda a: a - 1, lambda _: _, lambda c: c + 1)(1)
```
```
(0, 1, 2)
```

with result definition
```python
merged(print, lambda c: c + 1, return_from=1)(3)
merged(lambda a: a - 1, lambda _: _, lambda c: c + 1, return_from=slice(0, 3, 2))(2)
```
```
3
(1, 3)
```

merging the results
```python
mergely(
    lambda word: lambda a, b: f"_{a}_{b}",
    lambda word: word.capitalize(),
    lambda word: f"_{word}",
)("hello")
```
```
_Hello__hello
```

Repeat calls
```python
repeating(lambda line: f"{line}{line[-1]}", times(3))('Wry')
```
```
Wryyyy
```

Choose the function to execute
```python
square_or_module_of = on_condition(
    lambda number: number >= 0,
    lambda number: number ** 2,
    else_=abs
)

square_or_module_of(4)
square_or_module_of(-4)
```
```
16
4
```

### Partial application
Add arguments by calling
```python
@fragmentarily
def sentence_from(first: str, definition: str, second: str, sign: str = '!') -> str:
    return f"{first} {definition} {second}{sign}"


sentence_from("A lemon")("is not", sign='.')("an orange")
```
```
A lemon is not an orange.
```

after input
```python
to_message_template = "{} {}{}".format

post_partial(to_message_template, "world", '!')("Hello") 
```
```
Hello world!
```

using a function
```python
print_as_title = bind(print, 'sep', ' of ')
print_as_title("Table", "chairs")
```
```
Table of chairs
```

or pseudo operators
```python
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
```python
container = closed(to_message_template)
opened_container = container("Hello")

opened_container("container world", '!')
```
```
Hello container world!
```

using all possible ways
```python
post_container = closed(format_, closer=post_partial)

post_container('!')("Hello", "post container world")
```
```
Hello post container world!
```

### Data flow
Ignore the output value
```python
with_result("Forced result", print)("Input value") + "and something"
```
```
Input value
Forced result and something
```

via arguments
```python
returnly(print)("Input argument") + "and something"
```
```
Input argument
Input argument and something
```

or ignore input arguments
```python
eventually(print, 16)('Some', 'any', "arguments")
```
```
16
```

to get something
```python
taken("Something")('Some', 'any', "arguments")
```
```
Something
```

or forced binary answer
```python
yes('Some', 'any', "arguments")
no('Some', 'any', "arguments")
```
```
True
False
```

Force unpack from argument
```python
with_positional_unpacking(print)(range(4))
```
```
1 2 3
```

in dictionary form
```python
with_keyword_unpacking(lambda a, b: a + b)({'a': 5, 'b': 3})
```
```
8
```

or in argument pack form
```python
print_by = unpackly(print)

print_by(ArgumentPack(['Fish', "death"], {'sep': ' of '}))
print_by(ArgumentPack.of("Chair", "table", sep=' of '))
```
```
Fish of death
Chair of table
```

### Atomic operations
Transform without transforms
```python
returned(256)
```
```
256
```

Use synonyms to raise an error
```python
raise_(Exception("Something is wrong"))
```
```
Traceback ...
Exception: Something is wrong
```

to transform a context manager's context
```python
to_context(lambda file: file.read())(open("file.txt"))
```

to transform in a context manager's context
```python
with_context_by(taken(imaginary_transaction), lambda number: number / 0)(64)
```
```
Traceback ...
ImaginaryTransactionError: division by zero
```

to use syntax constructions
```python
call(print, 1, 2, 3, sep=' or ')
callmethod(dict(), 'get', None, "Default getting result")

data = dict()

setitem(data, "some-key", "some-value")
getitem(data, "some-key")
```
```
1 or 2 or 3
Default getting result
some-value
```

to use syntax operations
```python
execute_operation(60, '+', 4)
transform(str(), 'not')
```
```
64
True
```

by creating them
```python
operation = operation_by('+', 4)
operation(60)
```
```
64
```

using syntax operators
```python
difference_between = operation_of('-')
difference_between(55, 39)
```
```
16
```

### Annotating
Use annotation templates from the `annotations` package to shorten annotations
```python
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
```python
atomic_action # Callable[[Any], Any]

checker # Callable[[Any], bool]

decorator # Callable[[Callable], Callable]

event # Callable[[], Any]
```

or comments integrated as annotations
```python
add_five_and_print: dirty[reformer_of[number]]
```

or prepared `TypeVars`
```python
devil_function: Callable[
    [
        Callable[[Callable[[*ArgumentsT], ResourceT]], Callable[[ResourceT], ResultT]],
        Callable[[ResultT], ActionT],
        Callable[[Callable[[ErrorT], ErrorHandlingResultT]]],
        *ArgumentsT,
    ],
    ActionT | ErrorHandlingResultT
]
```

all of which can be viewed [here](https://github.com/TheArtur128/Pyhandling/blob/v3.0.0/pyhandling/annotations.py)


### Error handling
Handle errors that occur
```python
divide = rollbackable(operation_of('/'), returned)

divide(64, 4)
divide(8, 0)
```
```
16.0
division by zero
```

to receive through unpacking
```python
divide = with_error(operation_of('/'))

result, error = divide(16, 0)

print(result, error)
```
```
None division by zero
```

Optionally raise an error
```python
optional_raise = optional_raising_of(ZeroDivisionError)

optional_raise("Not a error")
optional_raise(Exception())
optional_raise(ZeroDivisionError("division by zero"))
```
```
Not a error
Exception()

Traceback ...
ZeroDivisionError: division by zero
```

### Calculation context
Break the chain of actions
```python
incremented_or_not: reformer_of[ContextRoot[number, Special[bad]]] = documenting_by(
    """
    Function to increase an input number if it is > 0.

    Takes as input a number wrapped in `ContextRoot`, using the `in_context`
    function or `ContextRoot(..., None)` directly.
    """
)(
    maybe(
        on_condition(operation_by('<', 0), taken(bad), else_=returned)
        |then>> operation_by('**', 2)
        |then>> operation_by('*', 1.3125)
    )
)


in_context(8) >= incremented_or_not
in_context(-16) >= incremented_or_not
```
```
84 on None
-16 on <negative Flag "bad">
```

in case of errors
```python
incremented: reformer_of[ContextRoot[number, Special[Exception]]]
incremented = until_error(
    operation_by('+', 10)
    |then>> operation_by('*', 2)
    |then>> (lambda number: number / (number - 28))
    |then>> operation_by('**', 2)
)


incremented(in_context(6))
incremented(in_context(4))
```
```
64.0 on None
28 on division by zero
```

with getting values
```python
root = incremented(in_context(4))

root.resource
root.context
```
```
28
division by zero
```

using unpacking
```python
number, context = incremented_or_not(in_context(-16))

print(number, context, sep=', ')
```
```
-16, <negative Flag "bad">
```

Display intermediate results
```python
"result is " + str(
    8 >= showly(
        operation_by('**', 2)
        |then>> operation_by('*', 1.3125)
        |then>> operation_by('+', 16)
    )
)
```
```
64
84.0
100.0
result is 100.0
```

pointwise
```python
showed(4) + 12
```
```
4
16
```

Combine compute contexts
```python
multi_context_incremented: reformer_of[
    ContextRoot[ContextRoot[Any, Special[bad]], Special[Exception]]
]
multi_context_incremented = documenting_by(
    """
    Function that increases a number using a tower from contexts.

    Each level of context evaluation requires a separate `ContextRoot` to be
    passed.
    """
)(
    (maybe |then>> until_error)(
        operation_by('+', 6)
        |then>> bad_when(operation_by('<', 0)) # Shortcut to optionally return `bad`
        |then>> (lambda number: number / (number - 10))
        |then>> operation_by('+', 5)
    )
)


in_context(in_context(5)) >= multi_context_incremented
in_context(in_context(-14)) >= multi_context_incremented
in_context(in_context(4)) >= multi_context_incremented
```
```
16.0 on None on None
-8 on <negative Flag "bad"> on None
10 on None on division by zero
```

indicating special behavior
```python
in_context(ContextRoot(5, bad)) >= multi_context_incremented
```
```
5 on <negative Flag "bad"> on None
```

using one `Context Root` level for different context calculations
```python
context_crossing_incremented: reformer_of[ContextRoot[number, Special[bad | Exception]]]
context_crossing_incremented = documenting_by(
    """
    Function that increases a number using two compute contexts with one
    `ContextRoot`.
    """
)(
    maybe(
        operation_by('+', 4)
        |then>> bad_when(operation_by('<=', 0))
        |then>> operation_by('*', 2)
    )
    |then>> until_error(
        operation_by('-', 14)
        |then>> (lambda n: n / (n - 2))
    )
    |then>> saving_context( # Calculation context without effect
        operation_by('+', 0.25)
        |then>> operation_by('*', 4)
    )
)


context_crossing_incremented(in_context(-4))
context_crossing_incremented(in_context(4))
context_crossing_incremented(in_context(8))
```
```
4.5 on <negative Flag "bad">
9.0 on division by zero
6.0 on None
```
### Batteries
Use out-of-the-box functions to abstract from input arguments
```python
take(256)(1, 2, 3)
event_as(execute_operation, 30, '+', 2)(1, 2, 3)
```
```
256
32
```

to create a collection via call
```python
collection_from(1, 2, 3)
```
```
(1, 2, 3)
```

to connect collections
```python
summed_collection_from((1, 2), (3, 4))
```
```
(1, 2, 3, 4)
```

to manage collection nesting
```python
wrap_in_collection(8)
open_collection_items(((1, 2), [3], 4))
```
```
(8, )
(1, 2, 3, 4)
```

to represent something as a collection
```python
as_collection(64)
as_collection([1, 2, 3])
```
```
(64, )
(1, 2, 3)
```

to confirm something multiple times
```python
runner = times(3)
tuple(runner() for _ in range(8))
```
```
(True, True, True, False, True, True, True, False)
```

to raise only a specific error
```python
optional_raise = optional_raising_of(ZeroDivisionError)

optional_raise(TypeError())
optional_raise(ZeroDivisionError("can't divide by zero"))
```
```
TypeError()

Traceback ...
ZeroDivisionError: can't divide by zero
```

to execute operations
```python
operation_by('*', 4)(64)
callmethod(', ', 'join', ("first", "second"))
```
```
256
first, second
```

to decoratively create action chains
```python
next_action_decorator_of(operation_by('**', 4))(operation_by('+', 1))(3)
previous_action_decorator_of(operation_by('+', 2))(operation_by('**', 2))(6)
```
```
256
64
```

to stop the chain when an error occurs
```python
breakable_chain = chain_breaking_on_error_that(isinstance |by| ZeroDivisionError)(
    (execute_operation |by* ('+', 4)) |then>> div_by_zero
)

breakable_chain(12)
```
```
BadResourceError('Resource "16" could not be handled due to ZeroDivisionError: division by zero')
```

to use shortcuts of routine options
```python
yes(1, 2, 3)
no(1, 2, 3)
```
```
True
False
```

### Immutable classes
Create immutable classes
```python
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
```python
original.some_attr = "some value"
```
```
Traceback ...
AttributeError: Type CallingPublisher is immutable
```

and automatically clone without manual creation
```python
other = original.with_follower(operation_by('**', 4) |then>> print)

original.followers
other.followers
```
```
(<built-in function print>,)
(<built-in function print>, ActionChain(...))
```

what would eventually
```python
other(4)
```
```
4
256
```

### Debugging
Display intermediate results
```python
showly(total_sum)([128, [100, 28]])
```
```
[128, [100, 28]]
(128, 128)
256
```

by different ways
```python
logger = Logger(is_date_logging=True)

showly(total_sum, writer=logger)([[2, 10], [15, 15]])

print(*logger.logs, sep='\n')
```
```
[2023-01-24 21:38:28.791516] [[2, 10], [15, 15]]
[2023-01-24 21:38:28.791516] (12, 30)
[2023-01-24 21:38:28.791516] 42
```