## Pyhandling
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

### Installation
`pip install pyhandling`

### Example

```python
from functools import partial
from typing import Iterable

from pyhandling import *
from pyhandling.checkers import Negationer, TypeChecker, UnionChecker, LengthChecker


main = (
    take(range(-10, 0))
    |then>> additionally(on_condition(
        Negationer(TypeChecker(Iterable)),
        separately(
            take(TypeError("Input data must be iterable collection."))
            |then>> raise_
        ),
    ))
    |then>> additionally(partial(
        map(
            on_condition(
                Negationer(TypeChecker(int | float)),
                separately(
                    take(TypeError("Elements of the input collection must be numbers."))
                    |then>> raise_
                ),
            )
        )
    ))
    |then>> CollectionExpander(range(11))
    |then>> additionally(print)
    |then>> partial(
        filter,
        UnionChecker(
            lambda number: not number % 2,
            lambda number: number != 0,
            is_strict=True
        )
    )
    |then>> tuple
    |then>> additionally(print)
    |then>> partial(map, lambda number: number + 1)
    |then>> tuple
    |then>> on_condition(TypeChecker(Iterable) & LengthChecker(256), tuple, return_)
    |then>> additionally(print)
    |then>> sum
    |then>> print
    |then>> separately(exit)
)

if __name__ == '__main__':
    main()
```

**output**
```
(-10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
(-10, -8, -6, -4, -2, 2, 4, 6, 8, 10)
(-9, -7, -5, -3, -1, 3, 5, 7, 9, 11)
10
```
