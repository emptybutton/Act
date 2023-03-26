# Pyhandling
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

## Installation
`pip install pyhandling`

## Examples
### Execution flow
Combine functions into a chain of calls

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
action_binding_of(lambda b: b / 2)(lambda: a + 10)(6)
left_action_binding_of(lambda: a + 10)(lambda b: b / 2)(6)
```
```
8
8
```

or via templates
```python
4 >= action_inserting_in(... |then>> (lambda a: a * 10) |then>> ...)(
    lambda number: number + 4
)
```
```
84
```

Merge them
```python
merged(lambda a: a - 1, lambda _: _, lambda c: c + 1)(1)
```
```
(0, 1, 2)
```

with result definition
```python
merged(print, lambda c: c + 1, return_from=1)(1)
```
```
1
2
```

or merging the results
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
sentence_from = fragmentarily(
    lambda first, definition, second, sign='.': f"{first} {definition} {second}{sign}"
)

sentence_from("Hello")('from')("the world")
sentence_from("Hello", 'to')("the world", sign='!')
sentence_from("Lemon", "is not", sign=str())("an orange")
```
```
Hello from the world.
Hello to the world!
Lemon is not an orange
```

after input
```python
to_message_template = "{} {}{}".format

post_partial(to_message_template, "world", '!')("Hello") 
```
```
Hello world!
```

using the function
```python
print_as_title = bind(print, 'sep', ' of ')
print_as_title("Ocean", "stones")
```
```
Ocean of stones
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
to_context(lambda file: file.read())(open("some-image.png"))
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

or prepared `TypeVar`s
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

See everything [here](https://github.com/TheArtur128/Pyhandling/blob/v3.0.0/pyhandling/annotations.py)


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

in the form of their constant expectation
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
Break the chain of actions when a "bad" resource occurs
```python
square_or_not_of: Callable[[number], number | BadResourceWrapper] = documenting_by(
    """Function to square a number if it is >= 0."""
)(
    maybe(
        bad_resource_wrapping_on(operation_by('<', 0))
        |then>> operation_by('**', 2)
    )
)


square_or_not_of(8)
square_or_not_of(-16)
```
```
64
<Wrapper of bad -16>
```

with the possibility of returning a "bad" resource
```python
main: dirty[reformer_of[number]] = optionally_exponentiate |then>> optionally_get_bad_resource_from

main(8)
main(-16)
```
```
64
-16
```

You can also interrupt by returning an error proxy that stores the error </br>that occurred while processing this resource and the resource itself
```python
from pyhandling.annotations import reformer_of


div_by_zero: reformer_of[number] = documenting_by(
    """Function for dividing an input number by zero."""
)(
    post_partial(execute_operation, '/', 0)
)


main: Callable[[number], number | BadResourceError] = (
    returnly_rollbackable(div_by_zero, take(True))
)


main(256)
```
```
BadResourceError('Resource "256" could not be handled due to ZeroDivisionError: division by zero')
```

with corresponding possibilities
```python
main: reformer_of[number] = (
    partial(map |then>> maybe, returnly_rollbackable |by| take(True))(
        post_partial(execute_operation, '*', 2)
        |then>> div_by_zero
    )
    |then>> optionally_get_bad_resource_from
)


main(16)
```
```
32
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