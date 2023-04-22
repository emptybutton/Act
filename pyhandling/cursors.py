from dataclasses import dataclass
from functools import partial, reduce, wraps
from itertools import count
from inspect import Signature, Parameter, stack
from operator import (
    call, not_, add, attrgetter, pos, neg, invert, gt, ge, lt, le, eq, ne, sub,
    mul, floordiv, truediv, mod, or_, lshift, is_, is_not, getitem, contains,
    xor, rshift, matmul, setitem
)
from typing import (
    Iterable, Callable, Any, Mapping, Self, Tuple, Optional, Literal
)

from pyannotating import Special

from pyhandling.annotations import (
    merger_of, event_for, ResultT, reformer_of, P, ObjectT
)
from pyhandling.arguments import ArgumentPack
from pyhandling.branching import ActionChain, binding_by, on, then
from pyhandling.contexting import contextual
from pyhandling.data_flow import with_result, by, to
from pyhandling.errors import ActionCursorError
from pyhandling.flags import flag_enum_of, nothing, flag
from pyhandling.monads import reading, saving_context, considering_context
from pyhandling.partials import flipped, rpartial, rwill, will
from pyhandling.structure_management import tfilter, groups_in
from pyhandling.synonyms import with_keyword, collection_of
from pyhandling.tools import property_to


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
class _OperationModel:
    sign: str
    priority: int | float


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
    binary_operation = flag("binary_operation")
    single_operation = flag("single_operation")
    operation = binary_operation | single_operation
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
    _sign: bool = False

    def __init__(
        self,
        *,
        parameters: Iterable[_ActionCursorParameter] = tuple(),
        actions: ActionChain = ActionChain(),
        previous: Optional[Self] = None,
        nature: contextual[_ActionCursorNature.flags, Any] = contextual(
            _ActionCursorNature.set_by_initialization,
        ),
        internal_repr: str = '...'
    ):
        self._parameters = tuple(sorted(
            set(parameters),
            key=attrgetter("priority"),
        ))
        self._actions = actions
        self._previous = previous
        self._nature = nature
        self._internal_repr = internal_repr

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

    @property
    def _adapted_internal_repr(self) -> str:
        return self.__get_adapted_internal_repr()

    @property
    def _single_adapted_internal_repr(self) -> str:
        return self.__get_adapted_internal_repr(single=True)

    def __repr__(self) -> str:
        return f"<action({{}}): {self._internal_repr}>".format(
            ', '.join(map(attrgetter('name'), self._parameters))
        )

    def __bool__(self) -> bool:
        return self._sign

    def __iter__(self) -> _ActionCursorUnpacking:
        return _ActionCursorUnpacking(self)

    def __len__(self) -> Literal[1]:
        return 1

    def __call__(self, *args) -> Any:
        if len(self._actions) == 0:
            return (
                self
                ._with_packing_of(args, by=tuple)
                ._with(internal_repr=(
                    f"({', '.join(map(self._repr_of, args))}"
                    f"{', ' if len(args) <= 1 else str()})"
                ))
            )

        elif self._nature.value == (
            _ActionCursorNature.vargetting
            | _ActionCursorNature.set_by_initialization
        ):
            return self._(*args)

        if len(args) > len(self._parameters):
            raise ActionCursorError(
                f"Extra arguments: "
                f"{', '.join(map(str, args[len(self._parameters):]))}"
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
        return self._with_calling_by(*args, **kwargs)._with(
            internal_repr=f"{self._adapted_internal_repr}({{}})".format(
                ', '.join(map(self._repr_of, args))
                + (', ' if args and kwargs else str())
                + ', '.join(
                    f"{key}={self._repr_of(arg)}"
                    for key, arg in kwargs.items()
                )
            )
        )

    @_generation_transaction
    def set(self, value: Any) -> Self:
        nature, place = self._nature

        if nature != (
            _ActionCursorNature.attrgetting | _ActionCursorNature.itemgetting
        ):
            raise ActionCursorError(
                "Setting a value when there is nowhere to set"
            )

        return (
            self
            ._with_setting(
                value,
                in_=place,
                by=(
                    setattr
                    if nature == _ActionCursorNature.attrgetting
                    else setitem
                ),
                return_as=(
                    getattr
                    if nature == _ActionCursorNature.attrgetting
                    else getitem
                ),
            )
            ._with(internal_repr=(
                f"({self._internal_repr} := {self._repr_of(value)})",
            ))
        )

    def keys(self):
        return (f"{self._unpacking_key_template}_of_{id(self)}", )

    @_generation_transaction
    def __getitem__(self, key: Special[Self | Tuple[Special[Self]]]) -> Self:
        if self._is_keyword_for_unpacking(key):
            return self._with(
                internal_repr=f"**{self._single_adapted_internal_repr}"
            )

        keys = key if isinstance(key, tuple) else (key, )
        formatted_keys = f"[{', '.join(map(self._repr_of, keys))}]"

        if len(self._actions) == 0:
            return (
                self
                ._with_packing_of(keys, by=list)
                ._with(
                    nature=contextual(_ActionCursorNature.packing, key),
                    internal_repr=formatted_keys
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
            ._with_calling_by(*keys)
            ._with(
                nature=contextual(_ActionCursorNature.itemgetting, key),
                internal_repr=f"{self._adapted_internal_repr}{formatted_keys}",
            )
        )

    @_generation_transaction
    def __getattr__(self, name: str) -> Self:
        if len(self._actions) == 0:
            nature = _ActionCursorNature.vargetting
            cursor = self._with(
                to(self._external_value_in(name)),
                internal_repr=name,
            )
        else:
            nature = _ActionCursorNature.attrgetting
            cursor = self._with(
                rwill(getattr)(
                    name[:-1]
                    if (
                        name[:-1] in self._overwritten_attribute_names
                        and name.endswith('_')
                    )
                    else name
                ),
                internal_repr=f"{self._adapted_internal_repr}.{name}",
            )

        return cursor._with(nature=contextual(nature, name))

    @classmethod
    def operated_by(cls, parameter: _ActionCursorParameter) -> Self:
        return cls(
            parameters=[parameter],
            actions=considering_context(
                reading(to(getitem |by| parameter.name))
            ),
            nature=contextual(_ActionCursorNature.returning),
            internal_repr=parameter.name,
        )

    @staticmethod
    def _external_value_in(name: str) -> Any:
        locals_ = stack()[1][0].f_back.f_back.f_locals

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
        internal_repr: Optional[str] = None,
    ) -> None:
        return type(self)(
            parameters=on(None, self._parameters)(parameters),
            actions=(
                action
                if isinstance(action, ActionChain)
                else ActionChain([action])
            ),
            previous=self._previous if previous is None else previous,
            nature=on(None, self._nature)(nature),
            internal_repr=on(None, self._internal_repr)(internal_repr),
        )

    def _with(
        self,
        action: Callable = ActionChain(),
        *,
        parameters: Optional[tuple[_ActionCursorParameter]] = None,
        previous: Optional[Self] = None,
        nature: Any = None,
        internal_repr: Optional[str] = None,
    ) -> Self:
        return self._of(
            self._actions >> saving_context(action),
            parameters=parameters,
            previous=previous,
            nature=nature,
            internal_repr=internal_repr,
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
    def _with_calling_by(
        self,
        *args: Special[Self],
        **kwargs: Special[Self],
    ) -> Self:
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
    def _with_partial_application_from(
        self,
        arguments: Iterable[Special[Self]],
    ) -> Self:
        arguments = tuple(arguments)

        if not arguments:
            return self

        return reduce(
            lambda cursor, argument: (
                cursor._merged_with(
                    argument.cursor,
                    by=lambda a, b: partial(a, *b)
                )
                if isinstance(argument, _ActionCursorUnpacking)
                else cursor._merged_with(argument, by=partial)
            ),
            (self, *arguments),
        )

    @_generation_transaction
    def _with_keyword_partial_application_by(
        self,
        argument_by_key: Mapping[str, Special[Self]],
    ) -> Self:
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
        by: Callable[[ObjectT, str, Any], Any],
        return_as: Callable[[ObjectT, str], Any],
    ) -> Self:
        place = in_
        set_ = by

        return (
            self._previous
            ._merged_with(value, by=(
                lambda a, b: return_as(with_result(a, set_)(a, place, b), place)
            ))
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

    def _is_keyword_for_unpacking(self, keyword: Special[str]) -> bool:
        return (
            isinstance(keyword, str)
            and keyword.startswith(self._unpacking_key_template)
        )

    def _update_signature(self) -> None:
        self.__signature__ = Signature(
            Parameter(cursor_parameter.name, Parameter.POSITIONAL_ONLY)
            for cursor_parameter in self._parameters
        )

    def _internal_repr_by(
        self,
        model: _OperationModel,
        *,
        on_left_side: bool = True,
    ) -> str:
        return (
            f"({self._internal_repr})"
            if (
                self._nature.value == _ActionCursorNature.operation
                and isinstance(self._nature.context, _OperationModel)
                and (gt if on_left_side else ge)(
                    self._nature.context.priority,
                    model.priority,
                )
            )
            else self._internal_repr
        )

    @staticmethod
    def _repr_of(value: Special[Self]) -> str:
        if isinstance(value, _ActionCursor):
            return value._internal_repr

        elif isinstance(value, _ActionCursorUnpacking):
            return f"*{value.cursor._single_adapted_internal_repr}"

        else:
            return str(value)

    def __get_adapted_internal_repr(self, *, single: bool = False) -> str:
        return (
            f"({self._internal_repr})"
            if (
                self._internal_repr == '...'
                or (
                    not single
                    and self._nature.value == _ActionCursorNature.operation
                )
            )
            else self._internal_repr
        )

    @staticmethod
    def __merging_by(
        operation: merger_of[Any],
        model: _OperationModel,
        *,
        is_right: bool = False,
    ) -> Callable[[Self, Special[Self]], Self]:
        def cursor_merger(cursor: Self, value: Special[Self]) -> Self:
            internal_repr = cursor._internal_repr_by(
                model,
                on_left_side=not is_right
            )

            return (
                cursor
                ._merged_with(
                    value,
                    by=operation if not is_right else flipped(operation),
                )
                ._with(
                    nature=contextual(
                        _ActionCursorNature.binary_operation,
                        model,
                    ),
                    internal_repr=(
                        (
                            f"{internal_repr} {model.sign} {{}}"
                            if not is_right
                            else f"{{}} {model.sign} {internal_repr}"
                        ).format(
                            value._internal_repr_by(model, on_left_side=is_right)
                            if isinstance(value, _ActionCursor)
                            else value
                        )
                    )
                )
            )

        return cursor_merger

    @staticmethod
    def __transformation_by(
        operation: Callable[[Special[Self]], ResultT],
        model: _OperationModel,
    ) -> reformer_of[Self]:
        def cursor_transformer(cursor: Self) -> Self:
            return cursor._with(
                operation,
                nature=contextual(_ActionCursorNature.single_operation, model),
                internal_repr=f"{model.sign}{cursor._internal_repr_by(model)}",
            )

        return cursor_transformer

    @staticmethod
    def __with_forced_sign(forced_sign: bool) -> reformer_of[Callable[P, Self]]:
        def decorator(action: Callable[P, Self]) -> Callable[P, Self]:
            @wraps(action)
            def action_with_forced_sign(*args: P.args, **kwargs: P.kwargs) -> Self:
                cursor = action(*args, **kwargs)
                cursor._sign = forced_sign

                return cursor

            return action_with_forced_sign

        return decorator

    is_ = __merging_by(is_, _OperationModel('is', 8))
    is_not = __merging_by(is_not, _OperationModel("is not", 8))
    in_ = __merging_by(contains, _OperationModel('in', 8))
    not_in = __merging_by(contains |then>> not_, _OperationModel('not in', 8))
    and_ = __merging_by(lambda a, b: a and b, _OperationModel('and', 9))
    or_ = __merging_by(lambda a, b: a or b, _OperationModel('or', 10))

    __pos__ = __transformation_by(pos, _OperationModel('+', 1))
    __neg__ = __transformation_by(neg, _OperationModel('-', 1))
    __invert__ = __transformation_by(invert, _OperationModel('~', 1))

    __pow__ = __merging_by(pow, _OperationModel('**', 0))
    __mul__ = __merging_by(mul, _OperationModel('*', 2))
    __floordiv__ = __merging_by(floordiv, _OperationModel('//', 2))
    __truediv__ = __merging_by(truediv, _OperationModel('/', 2))
    __matmul__ = __merging_by(matmul, _OperationModel('@', 2))
    __mod__ = __merging_by(mod, _OperationModel('%', 2))
    __add__ = __merging_by(add, _OperationModel('+', 3))
    __sub__ = __merging_by(sub, _OperationModel('-', 3))
    __lshift__ = __merging_by(lshift, _OperationModel('<<', 4))
    __rshift__ = __merging_by(rshift, _OperationModel('>>', 4))
    __and__ = __merging_by(and_, _OperationModel('&', 5))
    __xor__ = __merging_by(xor, _OperationModel('^', 6))

    def __or__(self, value: Special[ActionChain | Self]) -> Self:
        return (
            ActionChain([self, *value])
            if isinstance(value, ActionChain)
            else self.__merging_by(or_, _OperationModel('|', 7))(self, value)
        )

    __rpow__ = __merging_by(pow, _OperationModel('**', 0), is_right=True)
    __rmul__ = __merging_by(mul, _OperationModel('*', 2), is_right=True)
    __rfloordiv__ = __merging_by(floordiv, _OperationModel('//', 2), is_right=True)
    __rtruediv__ = __merging_by(truediv, _OperationModel('/', 2), is_right=True)
    __rmatmul__ = __merging_by(matmul, _OperationModel('@', 2), is_right=True)
    __rmod__ = __merging_by(mod, _OperationModel('%', 2), is_right=True)
    __radd__ = __merging_by(add, _OperationModel('+', 3), is_right=True)
    __rsub__ = __merging_by(sub, _OperationModel('-', 3), is_right=True)
    __rlshift__ = __merging_by(lshift, _OperationModel('<<', 4), is_right=True)
    __rrshift__ = __merging_by(rshift, _OperationModel('>>', 4), is_right=True)
    __rand__ = __merging_by(and_, _OperationModel('&', 5), is_right=True)
    __rxor__ = __merging_by(xor, _OperationModel('^', 6), is_right=True)
    __ror__ = __merging_by(or_, _OperationModel('|', 7), is_right=True)

    __gt__ = __with_forced_sign(False)(__merging_by(gt, _OperationModel('>', 8)))
    __lt__ = __with_forced_sign(False)(__merging_by(lt, _OperationModel('<', 8)))
    __ge__ = __with_forced_sign(False)(__merging_by(ge, _OperationModel('>=', 8)))
    __le__ = __with_forced_sign(False)(__merging_by(le, _OperationModel('>=', 8)))
    __ne__ = __with_forced_sign(True)(__merging_by(ne, _OperationModel('!=', 8)))
    __eq__ = __with_forced_sign(False)(__merging_by(eq, _OperationModel('==', 8)))


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
