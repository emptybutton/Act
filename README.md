## Pyhandling
Library for advanced continuous handling of anything

Provides tools to extend single call logic on a nearly unlimited scale</br>
You can even integrate the entire program logic into one call

### Installation
`pip install pyhandling`

### Usage examples

Basic example

```python
from functools import partial
from typing import Callable

from random import randint

from pyhandling import *


main: dirty[Callable[[int], str]] = showly(
    on_condition(
        lambda number: not 0 <= number <= 10,
        (
            "Input number must be positive and less than 11 but it is {}".format
            |then>> ValueError
            |then>> raise_
        ),
        else_=return_
    )
    |then>> mergely(take(execute_operation), return_, take('<<'), return_)
    |then>> mergely(
        take("{number} is {comparison_word} than 255".format),
        number=return_,
        comparison_word=lambda numebr: 'less' if numebr < 255 else 'more'
    )
)

if __name__ == '__main__':
    main(randint(-5, 10))
```

**output**
```
4
4
64
64 is less than 255
```

