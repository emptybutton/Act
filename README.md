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
print_multiplied_line_from = str |then>> (lambda x: x * 2) |then>> print
print_multiplied_line_from(23)
```

to later get

```python
2323
```

or you can do the same but call the function immediately

```python
23 >= str |then>> (lambda x: x * 2) |then>> print
```

and get the same result
```python
2323
```

### Currying
Change the interface of your functions to suit your current needs

```python
post_partial(lambda a, b, c: a + b + c, "world", '!')("Hello") 
```