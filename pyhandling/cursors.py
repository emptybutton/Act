from functools import partial
from itertools import count
from operator import call, not_, add, attrgetter, pos, neg, invert, gt, ge, lt, le, eq, ne, sub, mul, floordiv, truediv, mod, or_, and_, lshift
from typing import Iterable, Callable, Any, Mapping, Self

from pyannotating import Special

from pyhandling.annotations import one_value_action, merger_of, event_for
from pyhandling.atoming import atomically
from pyhandling.branching import ActionChain
from pyhandling.errors import ActionCursorError
from pyhandling.structure_management import tfilter, groups_in


__all__ = (
    "action_cursor_by",
    "priority_of",
    'a',
    'b',
    'c',
    'd',
    'e',
    'g',
    'h',
    'm',
    'n',
    'o',
    'p',
    'q',
    'r',
    's',
    'u',
    'v',
    'w',
    'x',
    'y',
    'z',
)


@dataclass(frozen=True)
class _ActionCursorParameter:
    name: str
    priority: int | float


class _ActionCursorOperation:
    def __get__(self, instance: "_ActionCursor", owner: "Type[_ActionCursor]") -> Self:
        return partial(self, instance)


class _ActionCursorBinaryOperation(_ActionCursorOperation):
    def __init__(self, operation: merger_of[Any]):
        self._operation = operation

    def __call__(self, first: Special["_ActionCursor"], second: Special["_ActionCursor"]) -> "_ActionCursor":
        if not isinstance(first, _ActionCursor) and isinstance(second, _ActionCursor):
            first, second = second, first
        elif not isinstance(first, _ActionCursor) and not isinstance(second, _ActionCursor):
            raise ActionCursorError("Absence of any \"_ActionCursor\"")

        cursor = first
        other = second

        return cursor._merged_with(other, by=self._operation)


class _ActionCursorTransformationOperation(_ActionCursorOperation):
    def __init__(self, operation: one_value_action):
        self._operation = operation

    def __call__(self, cursor: "_ActionCursor") -> "_ActionCursor":
        return cursor._with(saving_context(self._operation))


class _ActionCursor:
    def __init__(
        self,
        parameters: Iterable[_ActionCursorParameter],
        actions: ActionChain = ActionChain(),
    ):
        self._parameters = tuple(sorted(set(parameters), key=attrgetter("priority")))
        self._actions = actions

        if len(self._parameters) == 0:
            raise ActionCursorError("Creating a cursor without parameters")

        groups_with_same_priority = tfilter(
            lambda group: len(group) > 1,
            groups_in(self._parameters, attrgetter("priority")),
        )

        if len(groups_with_same_priority) != 0:
            raise ActionCursorError(
                "parameters with the same priority: {}".format(
                    ', '.join(map(str, groups_with_same_priority))
                )
            )

        self._update_signature()

    def __bool__(self) -> bool:
        return len(self._actions) != 0

    def __call__(self, *args) -> Any:
        if len(args) > len(self._parameters):
            raise ActionCursorError(
                f"Extra arguments: {', '.join(map(str, args[len(self._parameters):]))}"
            )
        
        elif len(args) == len(self._parameters):
            return self._run(contextual(
                nothing,
                when=dict(zip(map(attrgetter('name'), self._parameters), args))
            )).value

        elif len(args) < len(self._parameters):
            return partial(self, *args)

    def _run(self, root: contextual[Any, Mapping[str, Any]]) -> contextual:
        return self._actions(root)

    @to_clone
    def _of(self, action: Callable) -> None:
        self._actions = ActionChain([action])
        self._update_signature()

    def _with(self, action: Callable) -> Self:
        return self._of(self._actions >> action)

    def _merged_with(self, other: Special[Self], *, by: merger_of[Any]) -> Self:
        operation = by

        return (
            type(self)(
                self._parameters + other._parameters,
                ActionChain([lambda root: contextual(
                    operation(self._run(root).value, other._run(root).value),
                    when=root.context,
                )]),
            )
            if isinstance(other, _ActionCursor)
            else self._with(saving_context(operation |by| other))
        )

    def _update_signature(self) -> None:
        self.__signature__ = Signature(
            Parameter(cursor_parameter.name, Parameter.POSITIONAL_ONLY)
            for cursor_parameter in self._parameters
        )

    is_ = _ActionCursorBinaryOperation(is_)
    is_not = _ActionCursorBinaryOperation(is_not)
    or_ = _ActionCursorBinaryOperation(lambda a, b: a or b)
    and_ = _ActionCursorBinaryOperation(lambda a, b: a and b)

    __getitem__ = _ActionCursorBinaryOperation(getitem)
    __contains__ = _ActionCursorBinaryOperation(contains)

    __add__ = _ActionCursorBinaryOperation(add)
    __sub__ = _ActionCursorBinaryOperation(sub)
    __mul__ = _ActionCursorBinaryOperation(mul)
    __floordiv__ = _ActionCursorBinaryOperation(floordiv)
    __truediv__ = _ActionCursorBinaryOperation(truediv)
    __mod__ = _ActionCursorBinaryOperation(mod)
    __pow__ = _ActionCursorBinaryOperation(pow)
    __or__ = _ActionCursorBinaryOperation(or_)
    __xor__ = _ActionCursorBinaryOperation(xor)
    __and__ = _ActionCursorBinaryOperation(and_)
    __lshift__ = _ActionCursorBinaryOperation(lshift)
    __rshift__ = _ActionCursorBinaryOperation(rshift)

    __radd__ = _ActionCursorBinaryOperation(flipped(add))
    __rsub__ = _ActionCursorBinaryOperation(flipped(sub))
    __rmul__ = _ActionCursorBinaryOperation(flipped(mul))
    __rfloordiv__ = _ActionCursorBinaryOperation(flipped(floordiv))
    __rtruediv__ = _ActionCursorBinaryOperation(flipped(truediv))
    __rmod__ = _ActionCursorBinaryOperation(flipped(mod))
    __rpow__ = _ActionCursorBinaryOperation(flipped(pow))
    __ror__ = _ActionCursorBinaryOperation(flipped(or_))
    __rxor__ = _ActionCursorBinaryOperation(flipped(xor))
    __rand__ = _ActionCursorBinaryOperation(flipped(and_))

    __gt__ = _ActionCursorBinaryOperation(gt)
    __ge__ = _ActionCursorBinaryOperation(ge)
    __lt__ = _ActionCursorBinaryOperation(lt)
    __le__ = _ActionCursorBinaryOperation(le)
    __eq__ = _ActionCursorBinaryOperation(eq)
    __ne__ = _ActionCursorBinaryOperation(ne)

    __pos__ = _ActionCursorTransformationOperation(pos)
    __neg__ = _ActionCursorTransformationOperation(neg)
    __invert__ = _ActionCursorTransformationOperation(invert)


def action_cursor_by(
    name: str,
    *,
    priority: int | float | event_for[int | float] = next |by| count()
) -> _ActionCursor:
    if callable(priority):
        priority = priority()

    return _ActionCursor([_ActionCursorParameter(name, priority)])


def priority_of(cursor: _ActionCursor) -> int | float:
    if cursor:
        raise ActionCursorError("Getting a priority of an active cursor")

    return cursor._parameters[0].priority


# Without `i`, `j`, `k` and `t`
a = action_cursor_by('a')
b = action_cursor_by('b')
c = action_cursor_by('c')
d = action_cursor_by('d')
e = action_cursor_by('e')
g = action_cursor_by('g')
h = action_cursor_by('h')
m = action_cursor_by('m')
n = action_cursor_by('n')
o = action_cursor_by('o')
p = action_cursor_by('p')
q = action_cursor_by('q')
r = action_cursor_by('r')
s = action_cursor_by('s')
u = action_cursor_by('u')
v = action_cursor_by('v')
w = action_cursor_by('w')
x = action_cursor_by('x')
y = action_cursor_by('y')
z = action_cursor_by('z')