# Pyhandling
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

## Installation
`pip install pyhandling`

## Usage examples
### Composition
Merge your functions into one

```python
from pyhandling import *


complemented_number = str |then>> (lambda line: line + '6') |then>> int
complemented_number(25)
```

to later get
```python
256
```

or you can do the same but call the function immediately
```python
25 >= str |then>> (lambda line: line + '6') |then>> int
```

and get the same result
```python
256
```

### Currying
Add additional arguments to function input arguments
```python
formattly_sum = "{} {}{}".format

post_partial(formattly_sum, "world", '!')("Hello") 
```

using pseudo operators
```python
(formattly_sum |to| "Hello")("world", '!')
(formattly_sum |to* ("Hello", "world"))('!')

(formattly_sum |by| '!')("Hello", "world")
```

or not necessarily now
```python
container = close(formattly_sum)
opened_container = container("Hello")

opened_container("world", '!')
```

using all possible ways
```python
post_container = close(formattly_sum, closer=post_partial)

post_container('!')("Hello", "world")
```

Eventually, they all return
```
Hello world!
```

### Interface control
Abstract the output value
```python
print(returnly(print)("Some input argument"))
```
```
Some input argument
Some input argument
```

or input values
```python
from functools import partial


eventually(partial(print, 16))(1, 2, 3)
```
```
16
```

### Atomic functions
Use synonyms for operators
```python
return_(256)
raise_(Exception("Something is wrong"))
```
```
256

Traceback ...
Exception: Something is wrong
```

for atomic operations
```python
execute_operation(60, '+', 4)
transform(str(), 'not')
```
```
64
True
```

for syntax operations
```python
call(range, 16)

getitem_of({"some-key": "some-value"}, "some-key")
```
```
range(16)
some-value
```

### Annotating
Use standart annotation templates from `annotations` package for routine cases
```python
from pyhandling.annotations import checker_of, reformer_of, merger_of

from pyannotating import number


is_number_even: checker_of[number] = lambda number: number % 2 == 0

add_hundert_to: reformer_of[number] = lambda number: number + 100

format_lines: merger_of[str] = "{first} {second}{end_symbol}".format
```

or annotations themselves
```python
from pyannotating import many_or_one

from pyhandling.annotations import handler, decorator


executing_of: Callable[[many_or_one[handler]], decorator] = ...
```

### Function building
Create functions by describing them
```python
total_sum: Callable[[Iterable[many_or_one[number]]], number] = documenting_by(
    """
    Function of summing numbers from the input collection or the sum of its
    subcollection.
    """
)(
    close(map |then>> tuple)(
        on_condition(isinstance |by| Iterable, sum, else_=return_)
    )
    |then>> sum
)
```

in several processing processes
```python
ratio_of_square_to_full: reformer_of[number] = documenting_by(
    """
    Function of getting the ratio of the square of the input number to the
    input number to the power of its value.
    """
)(
    mergely(
        take(execute_operation),
        mergely(
            take(execute_operation),
            return_,
            take('*'),
            return_
        ),
        take('/'),
        mergely(
            take(execute_operation),
            return_,
            take('**'),
            return_
        )
    )
)
```

or in an indefinite number of iterative executions
```python
from pyhandling.annotations import dirty


increase_up_to_ten: dirty[reformer_of[number]] = documenting_by(
    """
    Function that prints numbers between the input number and 10 inclusive and
    returns 10.
    """
)(
    recursively(
        returnly(print) |then>> post_partial(execute_operation, '+', 1),
        post_partial(execute_operation, '<', 10)
    )
    |then>> returnly(print)
)


increase_up_to_ten(8)
```
```
8
9
10
```

### Chain breaking
Forcibly break the chain of actions
```python
optionally_exponentiate: Callable[[number], number | BadResourceWrapper] = documenting_by(
    """Function of exponentiation of the input number if it is > 0."""
)(
    maybe(
        on_condition(
            post_partial(execute_operation, '<', 0),
            BadResourceWrapper,
            else_=return_
        )
        |then>> post_partial(execute_operation, '**', 2)
    )
)


optionally_exponentiate(-16)
```
```
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

other(4)
```
```
(<built-in function print>,)
(<built-in function print>, ActionChain(...))
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