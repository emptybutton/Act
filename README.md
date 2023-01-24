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
formattly_sum = lambda first, second, end_symbol: first + ' ' + second + end_symbol

post_partial(formattly_sum, "world", '!')("Hello") 
```

not necessarily now
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

### Atomicity
Use any python atomic operations as functions
```python
(lambda reource: raise_(reource) if isinstance(reource, Exception) else return_)("no error") # "no error"

execute_operation(60, '+', 4) # 64

transform_by('not', str()) # True

call(range, 16) # range(16)

getitem_of({"some-key": "some-value"}, "some-key") # "some-value"
```

### Annotating
Use standart annotation templates for routine cases
```python
is_number_even: checker_of[number] = lambda number: number % 2 == 0

add_hundert_to: reformer_of[number] = lambda number: number + 100

format_lines: merger_of[str] = lambda first_line, second_line: first_line + ' ' + second_line + '!'
```

or annotations themselves
```python
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
        on_condition(post_partial(isinstance, Iterable), sum, else_=return_)
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

-16 >= optionally_exponentiate |then>> print
```
```
<Wrapper of bad -16>
```

with the possibility of returning a "bad" resource
```python
main: dirty[reformer_of[number]] = optionally_exponentiate |then>> optionally_get_bad_resource_from

8 >= optionally_exponentiate |then>> print
-16 >= optionally_exponentiate |then>> print
```
```
64
-16
```

You can also interrupt by returning an error proxy that stores the error </br>that occurred while processing this resource and the resource itself
```python
div_by_zero: reformator_of[number] = post_partial(execute_operation, '/', 0)

main: Callable[[number], number | BadResourceError] = (
    post_partial(rollbackble, BadResourceError)(div_by_zero)
)

256 >= main |then>> print
```
```
BadResourceError('Resource "256" could not be handled due to ZeroDivisionError: division by zero')
```

with corresponding possibilities
```python
main = reformator_of[number] = (
    post_partial(execute_operation, '/', 0)
    |then>> optionally_get_bad_resource_from
)
16 >= main |then>> print
```
```
16
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