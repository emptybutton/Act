## Act
Library for dynamic functional programming and more.

Enter this command and go to the [documentation](https://github.com/TheArtur128/Pyhandling/blob/main/DOCS.md):
```
pip install pyhandling
```

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
