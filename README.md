## Act
Library for dynamic functional programming and more.

Enter this command and go to the [documentation](https://github.com/TheArtur128/Act/blob/main/DOCS.md):
```
pip install act4
```

### Overview
```py
from typing import Optional, Callable

from act import *


def division_between(a: int, b: int) -> int | bad[str]:
    if a == 0 or b == 0:
        return bad("division by zero")

    return a / b


WithNumber = type(number=N)

WithMultiplication = type(multiplication=M)
WithDivision = type(division=D)

Result = WithMultiplication[N] & WithDivision[N]


@fbind_by(... |then>> on(None, bad("something is missing")))
@do(maybe, optionally, for_input=optionally)
def func(do: Do, a: WithNumber[Optional[int]], b: WithNumber[Optional[int]]) -> Result[int]:
    maybe, optionally = do

    first_number = optionally.same(a.number)
    second_number = optionally.same(b.number)
    
    division = maybe(division_between)(first_number, second_number)
    multiplication = first_number * second_number

    return Result(multiplication, division)


# As a result, `func` has this type.
func: Callable[
    [Optional[WithNumber[Optional[int]]], Optional[WithNumber[Optional[int]]]],
    Result[int] | bad[str],
]

assert func(WithNumber(16), WithNumber(2)) == obj(multiplication=32, division=8)
assert func(WithNumber(16), WithNumber(0)) == bad("division by zero")
assert func(WithNumber(16), WithNumber(None)) == bad("something is missing")
assert func(WithNumber(16), None) == bad("something is missing")


class RawResult:
    def __init__(self, multiplication: int, division: int) -> None:
        self.multiplication = multiplication
        self.division = division


assert (
    Result(32, 8)
    == RawResult(32, 8)
    == WithMultiplication(32) & WithDivision(8)
    == obj(multiplication=32, division=8)
)

```
