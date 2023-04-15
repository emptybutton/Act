from functools import partial
from itertools import count
from operator import call, not_, add, attrgetter, pos, neg, invert, gt, ge, lt, le, eq, ne, sub, mul, floordiv, truediv, mod, or_, and_, lshift
from typing import Iterable, Callable, Any, Mapping, Self

from pyannotating import Special

from pyhandling.annotations import one_value_action, merger_of
from pyhandling.atoming import atomically
from pyhandling.branching import ActionChain


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


class _ActionCursorBinaryOperation:
    def __init__(self, operation: merger_of[Any]):
        self._operation = operation

    def __call__(self, first: Special["_ActionCursor"], second: Special["_ActionCursor"]) -> "_ActionCursor":
        if not isinstance(first, _ActionCursor) and isinstance(second, _ActionCursor):
            first, second = second, first
        elif not isinstance(first, _ActionCursor) and not isinstance(second, _ActionCursor):
            raise ActionCursorError("Absence of any \"_ActionCursor\"")

        cursor = first
        other = second

        if not cursor:
            cursor = cursor._of(reading(taken(
                getitem |by| cursor._parameters[0].name
            )))

        return (
            cursor._of(dynamically(self._operation, cursor._run, other._run))
            if isinstance(other, _ActionCursor)
            else cursor._with(saving_context(operation |by| other))
        )


class _ActionCursorTransformationOperation:
    def __init__(self, operation: one_value_action):
        self._operation = operation

    def __call__(self, cursor: "_ActionCursor") -> "_ActionCursor":
        return cursor._with(self._operation)


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
            groupby(self._parameters, attrgetter("priority")),
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
        if len(args) < len(self._parameters):
            raise ActionCursorError(
                f"Extra arguments: {self._parameters[len(args) - 1:]}"
            )
        
        elif len(args) == len(self._parameters):
            return self._run(contextual(
                nothing,
                when=dict(zip(map(attrgetter('name'), self._parameters), args))
            ))

        elif len(args) > len(self._parameters):
            return partial(self, *args)

    def _run(root: contextual[Any, Mapping[str, Any]]):
        return self._actions(root)

    @to_clone
    def _of(self, action: Callable) -> None:
        self._actions = ActionChain([action])
        self._update_signature()

    def _with(self, action: Callable) -> Self:
        return self._of(self._actions >> action)

    def _update_signature(self) -> None:
        self.__signature__ = Signature(
            Parameter(cursor_parameter.name, Parameter.POSITIONAL_ONLY)
            for cursor_parameter in self._parameters
        )

    is_ = atomically(_ActionCursorOperation(is_))
    is_not = atomically(_ActionCursorOperation(is_not))
    or_ = atomically(_ActionCursorOperation(or_))
    and_ = atomically(_ActionCursorOperation(and_))

    __getitem__ = atomically(_ActionCursorOperation(getitem))
    __contains__ = atomically(_ActionCursorOperation(contains))

    __add__ = atomically(_ActionCursorOperation(add))
    __sub__ = atomically(_ActionCursorOperation(sub))
    __mul__ = atomically(_ActionCursorOperation(mul))
    __floordiv__ = atomically(_ActionCursorOperation(floordiv))
    __truediv__ = atomically(_ActionCursorOperation(truediv))
    __mod__ = atomically(_ActionCursorOperation(mod))
    __pow__ = atomically(_ActionCursorOperation(pow))
    __or__ = atomically(_ActionCursorOperation(or_))
    __xor__ = atomically(_ActionCursorOperation(xor))
    __and__ = atomically(_ActionCursorOperation(and_))
    __lshift__ = atomically(_ActionCursorOperation(lshift))
    __rshift__ = atomically(_ActionCursorOperation(rshift))

    __radd__ = atomically(_ActionCursorOperation(flipped(add)))
    __rsub__ = atomically(_ActionCursorOperation(flipped(sub)))
    __rmul__ = atomically(_ActionCursorOperation(flipped(mul)))
    __rfloordiv__ = atomically(_ActionCursorOperation(flipped(floordiv)))
    __rtruediv__ = atomically(_ActionCursorOperation(flipped(truediv)))
    __rmod__ = atomically(_ActionCursorOperation(flipped(mod)))
    __rpow__ = atomically(_ActionCursorOperation(flipped(pow)))
    __ror__ = atomically(_ActionCursorOperation(flipped(or_)))
    __rxor__ = atomically(_ActionCursorOperation(xor))
    __rand__ = atomically(_ActionCursorOperation(flipped(and_)))

    __gt__ = atomically(_ActionCursorOperation(gt))
    __ge__ = atomically(_ActionCursorOperation(ge))
    __lt__ = atomically(_ActionCursorOperation(lt))
    __le__ = atomically(_ActionCursorOperation(le))
    __eq__ = atomically(_ActionCursorOperation(eq))
    __ne__ = atomically(_ActionCursorOperation(ne))

    __pos__ = atomically(_ActionCursorTransformationOperation(pos))
    __neg__ = atomically(_ActionCursorTransformationOperation(neg))
    __invert__ = atomically(_ActionCursorTransformationOperation(invert))


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