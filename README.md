## Pyhandling
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

### Example
```python
from functools import partial
from typing import Iterable

from pyhandling import ActionChain, HandlingNode, Brancher, EventAdapter, ErrorRaiser, CollectionExpander, Mapper, return_
from pyhandling.checkers import Negationer, TypeChecker, Aller


main = ActionChain(
    HandlingNode(Brancher(
        EventAdapter(ErrorRaiser(TypeError("Input data must be iterable collection."))),
        Negationer(TypeChecker(Iterable))
    )),
    HandlingNode(Mapper(
        Brancher(
            EventAdapter(ErrorRaiser(TypeError("Elements of the input collection must be numbers."))),
            Negationer(TypeChecker(int | float))
        )
    )),
    CollectionExpander(range(11)),
    HandlingNode(print),
    partial(
        filter,
        Aller(lambda number: not number % 2, lambda number: number != 0)
    ),
    tuple,
    HandlingNode(print),
    partial(map, lambda number: number + 1),
    Brancher(tuple, TypeChecker(Iterable) | TypeChecker(int | float), return_),
    HandlingNode(print),
    sum,
    print,
    EventAdapter(exit)
)

if __name__ == '__main__':
    main(range(-10, 0))
```

**output**
```
(-10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
(-10, -8, -6, -4, -2, 2, 4, 6, 8, 10)
(-9, -7, -5, -3, -1, 3, 5, 7, 9, 11)
10
```