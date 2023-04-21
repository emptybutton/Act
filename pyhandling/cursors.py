from dataclasses import dataclass
from enum import Enum, auto
from functools import partial, reduce, wraps, cached_property
from itertools import count
from inspect import Signature, Parameter, stack
from operator import call, not_, add, attrgetter, pos, neg, invert, gt, ge, lt, le, eq, ne, sub, mul, floordiv, truediv, mod, or_, and_, lshift, is_, is_not, getitem, contains, xor, rshift, matmul, setitem
from typing import Iterable, Callable, Any, Mapping, Self, NoReturn, Tuple, Optional, Literal

from pyannotating import Special

from pyhandling.annotations import one_value_action, merger_of, event_for, ResultT, reformer_of
from pyhandling.arguments import ArgumentPack
from pyhandling.branching import ActionChain, binding_by, on
from pyhandling.contexting import contextual
from pyhandling.data_flow import dynamically, with_result
from pyhandling.errors import ActionCursorError
from pyhandling.flags import flag_enum_of, nothing
from pyhandling.immutability import to_clone
from pyhandling.language import by, then, to
from pyhandling.monads import reading, saving_context, considering_context
from pyhandling.partials import flipped, rpartial, rwill, will, fragmentarily
from pyhandling.structure_management import tfilter, groups_in
from pyhandling.synonyms import with_keyword, collection_of
from pyhandling.tools import property_to
from pyhandling.utils import shown


__all__ = (
    "action_cursor_by",
    "priority_of",
    "act",
    '_',
    'a',
    'b',
    'c',
    'd',
    'e',
    'g',
    'h',
    'i',
    'j',
    'k',
    'l',
    'm',
    'n',
    'o',
    'p',
    'q',
    'r',
    's',
    't',
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


class _ActionCursorUnpacking:
    cursor = property_to("_cursor")

    def __init__(self, cursor: "_ActionCursor", *, was_unpacked: bool = False):
        self._cursor = cursor
        self._was_unpacked = was_unpacked

    def __next__(self) -> Self:
        if self._was_unpacked:
            raise StopIteration

        self._was_unpacked = True
        return self


@flag_enum_of
class _ActionCursorNature:
    attrgetting = ...
    vargetting = ...
    itemgetting = ...
    calling = ...
    packing = ...
    setting = ...
    binary_operation = ...
    single_operation = ...
    set_by_initialization = ...
    returning = ...


class _ActionCursor(Mapping):
    _unpacking_key_template: str = "__ActionCursor_keyword_unpacking"
    _overwritten_attribute_names: Tuple[str] = (
        '_',
        'set',
        "keys",
        'is_',
        "is_not",
        'or_',
        'and_',
    )

    def __init__(
        self,
        parameters: Iterable[_ActionCursorParameter] = tuple(),
        actions: ActionChain = ActionChain(),
        previous: Optional[Self] = None,
        nature: contextual[_ActionCursorNature.flags, Any] = contextual(
            _ActionCursorNature.set_by_initialization,
        ),
    ):
        self._parameters = tuple(sorted(set(parameters), key=attrgetter("priority")))
        self._actions = actions
        self._previous = previous
        self._nature = nature

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

    def __repr__(self) -> str:
        return f"ActionCursor({self._actions})"

    def __iter__(self) -> _ActionCursorUnpacking:
        return _ActionCursorUnpacking(self)

    def __len__(self) -> Literal[1]:
        return 1

    def __call__(self, *args) -> Any:
        if not self:
            return (
                self
                ._with_packing_of(args, by=tuple)
            )

        elif self._nature.value == (
            _ActionCursorNature.vargetting
            | _ActionCursorNature.set_by_initialization
        ):
            return self._(*args)

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

    @staticmethod
    def _generation_transaction(
        method: Callable[[Self, ...], Self],
    ) -> Callable[[Self, ...], Self]:
        return wraps(method)(lambda cursor, *args, **kwargs: (
            method(cursor, *args, **kwargs)._with(previous=cursor)
        ))

    @_generation_transaction
    def _(self, *args: Special[Self], **kwargs: Special[Self]) -> Self:
        return self._with_calling_by(*args, **kwargs)

    @_generation_transaction
    def set(self, value: Any) -> Self:
        nature, place = self._nature

        if nature != _ActionCursorNature.attrgetting | _ActionCursorNature.itemgetting:
            raise ActionCursorError("Setting a value when there is nowhere to set")

        return self._previous._with_setting(
            value,
            in_=place,
            by=setattr if nature is _ActionCursorNature.attrgetting else setitem,
        )

    def keys(self):
        return (f"{self._unpacking_key_template}_of_{id(self)}", )

    @_generation_transaction
    def __getitem__(self, key: Special[Self | Tuple[Special[Self]]]) -> Self:
            return self
        if self._is_keyword_for_unpacking(key):

        if not self:
            return (
                self
                ._with_packing_of(keys, by=list)
                ._with(
                    nature=contextual(_ActionCursorNature.packing, key),
                )
            )

        return (
            self
            ._with(
                will(getitem) |then>> binding_by(
                    collection_of
                    |then>> on(len |then>> (eq |by| 1), getitem |by| 0)
                    |then>> ...
                )
            )
            ._with_calling_by(*key if isinstance(key, tuple) else (key, ))
            ._with(nature=contextual(_ActionCursorNature.itemgetting, key))
        )

    @_generation_transaction
    def __getattr__(self, name: str) -> Self:
        if not self:
            nature = _ActionCursorNature.vargetting
            cursor = self._with(to(self._external_value_in(name)))
        else:
            nature = _ActionCursorNature.attrgetting
            cursor = self._with(rwill(getattr)(
                name[:-1]
                if (
                    name[:-1] in self._overwritten_attribute_names
                    and name.endswith('_')
                )
                else name
            ))

        return cursor._with(nature=contextual(nature, name))

    @classmethod
    def operated_by(cls, parameter: _ActionCursorParameter) -> Self:
        return cls(
            parameters=[parameter],
            actions=considering_context(
                reading(to(getitem |by| parameter.name))
            ),
            nature=contextual(_ActionCursorNature.returning),
        )

    @staticmethod
    def _external_value_in(name: str) -> Any:
        locals_ = stack()[1][0].f_back.f_locals

        return locals_[name] if name in locals_.keys() else eval(name)

    def _run(self, root: contextual[Any, Mapping[str, Any]]) -> contextual:
        return self._actions(root)

    def _of(
        self,
        action: Special[ActionChain, Callable],
        *,
        parameters: Optional[tuple[_ActionCursorParameter]] = None,
        previous: Optional[Self] = None,
        nature: Optional[contextual[_ActionCursorNature.flags, Any]] = None,
    ) -> None:
        return type(self)(
            parameters=self._parameters if parameters is None else parameters,
            actions=action if isinstance(action, ActionChain) else ActionChain([action]),
            previous=self._previous if previous is None else previous,
            nature=self._nature if nature is None else nature,
        )

    def _with(
        self,
        action: Callable = ActionChain(),
        *,
        parameters: Optional[tuple[_ActionCursorParameter]] = None,
        previous: Optional[Self] = None,
        nature: Any = None,
    ) -> Self:
        return self._of(
            self._actions >> saving_context(action),
            parameters=parameters,
            previous=previous,
            nature=nature,
        )

    @_generation_transaction
    def _merged_with(self, other: Special[Self], *, by: merger_of[Any]) -> Self:
        operation = by

        cursor = (
            self._of(
                ActionChain([lambda root: contextual(
                    operation(self._run(root).value, other._run(root).value),
                    when=root.context,
                )]),
                parameters=self._parameters + other._parameters,
            )
            if isinstance(other, _ActionCursor)
            else self._with(rpartial(operation, other))
        )

        return cursor._with(nature=contextual(
            _ActionCursorNature.binary_operation,
            contextual(operation, other),
        ))

    @_generation_transaction
    def _with_calling_by(self, *args: Special[Self], **kwargs: Special[Self]) -> Self:
        return (
            self
            ._with_partial_application_from(args)
            ._with_keyword_partial_application_by(kwargs)
            ._with(call, nature=contextual(
                _ActionCursorNature.calling,
                when=ArgumentPack(args, kwargs),
            ))
        )

    @_generation_transaction
    def _with_partial_application_from(self, arguments: Iterable[Special[Self]]) -> Self:
        arguments = tuple(arguments)

        if not arguments:
            return self

        return reduce(
            lambda cursor, argument: (
                cursor._merged_with(argument.cursor, by=lambda a, b: partial(a, *b))
                if isinstance(argument, _ActionCursorUnpacking)
                else cursor._merged_with(argument, by=partial)
            ),
            (self, *arguments),
        )

    @_generation_transaction
    def _with_keyword_partial_application_by(self, argument_by_key: Mapping[str, Special[Self]]) -> Self:
        if not argument_by_key.keys():
            return self

        return reduce(
            lambda cursor, key_and_argument: (cursor._merged_with(
                key_and_argument[1],
                by=(
                    lambda a, b: partial(a, **b)
                    if self._is_keyword_for_unpacking(key_and_argument[0])
                    else flipped(with_keyword |to| key_and_argument[0]),
                ),
            )),
            (self, *argument_by_key.items()),
        )

    @_generation_transaction
    def _with_setting(
        self,
        value: Special[Self],
        *,
        in_: str,
        by: Callable[[Any, str, Any], Any]
    ) -> Self:
        place = in_
        set_ = by

        return (
            self
            ._merged_with(value, by=lambda a, b: with_result(b, set_)(a, place, b))
            ._with(nature=contextual(
                _ActionCursorNature.setting,
                contextual(value, place)
            ))
        )

    @_generation_transaction
    def _with_packing_of(
        self,
        items: Iterable[Special[Self]],
        *,
        by: Callable[[tuple], Iterable],
    ) -> Self:
        items = tuple(items)

        return (
            self
            ._with(to(collection_of))
            ._with_calling_by(*items)
            ._with(by, nature=contextual(
                _ActionCursorNature.packing,
                contextual(by, tuple(items))),
            )
        )

        return keyword.startswith(self._unpacking_key_template)
    def _is_keyword_for_unpacking(self, keyword: Special[str]) -> bool:

    def _update_signature(self) -> None:
        self.__signature__ = Signature(
            Parameter(cursor_parameter.name, Parameter.POSITIONAL_ONLY)
            for cursor_parameter in self._parameters
        )

    @staticmethod
    def __merging_by(operation: merger_of[Any]) -> Callable[[Self, Special[Self]], Self]:
        return lambda cursor, value: cursor._merged_with(value, by=operation)

    @staticmethod
    def __transformation_by(operation: Callable[[Special[Self]], ResultT]) -> reformer_of[Self]:
        return lambda cursor: cursor._with(
            operation,
            nature=contextual(_ActionCursorNature.single_operation, operation),
        )

    is_ = __merging_by(is_)
    is_not = __merging_by(is_not)
    in_ = __merging_by(contains)
    not_in = __merging_by(contains |then>> not_)
    or_ = __merging_by(lambda a, b: a or b)
    and_ = __merging_by(lambda a, b: a and b)

    __contains__ = __merging_by(contains)

    __add__ = __merging_by(add)
    __sub__ = __merging_by(sub)
    __mul__ = __merging_by(mul)
    __floordiv__ = __merging_by(floordiv)
    __truediv__ = __merging_by(truediv)
    __mod__ = __merging_by(mod)
    __pow__ = __merging_by(pow)
    __or__ = __merging_by(or_)
    __xor__ = __merging_by(xor)
    __and__ = __merging_by(and_)
    __matmul__ = __merging_by(matmul)
    __lshift__ = __merging_by(lshift)
    __rshift__ = __merging_by(rshift)

    __radd__ = __merging_by(flipped(add))
    __rsub__ = __merging_by(flipped(sub))
    __rmul__ = __merging_by(flipped(mul))
    __rfloordiv__ = __merging_by(flipped(floordiv))
    __rtruediv__ = __merging_by(flipped(truediv))
    __rmod__ = __merging_by(flipped(mod))
    __rpow__ = __merging_by(flipped(pow))
    __ror__ = __merging_by(flipped(or_))
    __rxor__ = __merging_by(flipped(xor))
    __rand__ = __merging_by(flipped(and_))
    __rmatmul__ = __merging_by(flipped(matmul))

    __gt__ = __merging_by(gt)
    __ge__ = __merging_by(ge)
    __lt__ = __merging_by(lt)
    __le__ = __merging_by(le)
    __eq__ = __merging_by(eq)
    __ne__ = __merging_by(ne)

    __pos__ = __transformation_by(pos)
    __neg__ = __transformation_by(neg)
    __invert__ = __transformation_by(invert)


def action_cursor_by(
    name: str,
    *,
    priority: int | float | event_for[int | float] = next |by| count()
) -> _ActionCursor:
    if callable(priority):
        priority = priority()

    return _ActionCursor.operated_by(_ActionCursorParameter(name, priority))


def priority_of(cursor: _ActionCursor) -> int | float:
    if len(cursor._parameters) > 1:
        raise ActionCursorError("Getting multicursor priority")

    elif len(cursor._parameters) == 0:
        raise ActionCursorError("Getting constant cursor priority")

    return cursor._parameters[0].priority


act = _ActionCursor()
_ = _ActionCursor()


a = action_cursor_by('a')
b = action_cursor_by('b')
c = action_cursor_by('c')
d = action_cursor_by('d')
e = action_cursor_by('e')
g = action_cursor_by('g')
h = action_cursor_by('h')
i = action_cursor_by('i')
j = action_cursor_by('j')
k = action_cursor_by('k')
l = action_cursor_by('l')
m = action_cursor_by('m')
n = action_cursor_by('n')
o = action_cursor_by('o')
p = action_cursor_by('p')
q = action_cursor_by('q')
r = action_cursor_by('r')
s = action_cursor_by('s')
t = action_cursor_by('t')
u = action_cursor_by('u')
v = action_cursor_by('v')
w = action_cursor_by('w')
x = action_cursor_by('x')
y = action_cursor_by('y')
z = action_cursor_by('z')