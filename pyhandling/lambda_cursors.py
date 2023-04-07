from collections import OrderedDict
from datetime import datetime
from functools import wraps, partial, cached_property, update_wrapper
from operator import itemgetter, call, not_, add, attrgetter, pos, neg, invert, gt, ge, lt, le, eq, ne, sub, mul, floordiv, truediv, mod, or_, and_, lshift
from typing import NamedTuple, Generic, Iterable, Tuple, Callable, Any, Mapping, Type, NoReturn, Optional, Self, TypeVar

from pyannotating import many_or_one, AnnotationTemplate, input_annotation, Special, method_of

from pyhandling.annotations import one_value_action, dirty, handler_of, ValueT, ContextT, ResultT, checker_of, ErrorT, action_for, merger_of, P, reformer_of, KeyT, MappedT
from pyhandling.arguments import ArgumentPack
from pyhandling.atoming import atomically
from pyhandling.binders import returnly, closed, right_closed, right_partial, eventually, unpackly
from pyhandling.branching import ActionChain, on, rollbackable, mergely, mapping_to_chain_of, mapping_to_chain, repeating, binding_by
from pyhandling.contexting import contextual, contextually, context_pointed
from pyhandling.data_flow import returnly
from pyhandling.errors import LambdaGeneratingError
from pyhandling.flags import flag, nothing, Flag, flag_to
from pyhandling.language import then, by, to
from pyhandling.partials import closed
from pyhandling.synonyms import returned
from pyhandling.tools import documenting_by, Clock


_attribute_getting = flag("_attribute_getting")
_item_getting = flag("_item_getting")
_method_calling_preparation = flag("_method_calling_preparation")
_forced_call = flag("_forced_call")


def _as_generator_validating(
    is_valid: checker_of["_LambdaGenerator"]
) -> reformer_of[method_of["_LambdaGenerator"]]:
    def wrapper(method: method_of["_LambdaGenerator"]) -> method_of["_LambdaGenerator"]:
        @wraps(method)
        def method_wrapper(generator: "_LambdaGenerator", *args, **kwargs) -> Any:
            if not is_valid(generator):
                raise LambdaGeneratingError(
                    "Non-correct generation action when "
                    f"{generator._last_action_nature.value}"
                )

            return method(generator, *args, **kwargs)

        return method_wrapper

    return wrapper


def _invalid_when(*invalid_natures: contextual) -> reformer_of[method_of["_LambdaGenerator"]]:
    return _as_generator_validating(
        lambda generator: generator._last_action_nature.value not in invalid_natures
    )


def _valid_when(*valid_natures: contextual) -> reformer_of[method_of["_LambdaGenerator"]]:
    return _as_generator_validating(
        lambda generator: generator._last_action_nature.value in valid_natures
    )


class _LambdaGenerator(Generic[ResultT]):
    def __init__(
        self,
        name: str,
        actions: Special[ActionChain, Callable] = ActionChain(),
        *,
        last_action_nature: contextual = contextual(nothing),
        is_template: bool = False
    ):
        self._name = name
        self._actions = ActionChain(as_collection(actions))
        self._last_action_nature = last_action_nature
        self._is_template = is_template

    def __repr__(self) -> str:
        return str(self._actions)

    @property
    def to(self) -> Self:
        return self._of(last_action_nature=contextual(_forced_call))

    @_valid_when(_attribute_getting, _item_getting)
    def set(self, value: Any) -> Self:
        if self._last_action_nature.value is _attribute_getting:
            return self.__with_setting(setattr, value)

        elif self._last_action_nature.value is _item_getting:
            return self.__with_setting(setitem, value)

        raise LambdaSettingError("Setting without place")

    def is_(self, value: Any) -> Self:
        return self._like_operation(operation_of('is'), value)

    def isnt(self, value: Any) -> Self:
        return self._like_operation(operation_of("is not"), value)

    def or_(self, value: Any) -> Self:
        return self._like_operation(operation_of('or'), value)

    def and_(self, value: Any) -> Self:
        return self._like_operation(operation_of('and'), value)

    def _not(self) -> Self:
        return self._with(not_)

    def _of(self, *args, is_template: Optional[bool] = None, **kwargs) -> Self:
        if is_template is None:
            is_template = self._is_template 

        return type(self)(self._name, *args, is_template=is_template, **kwargs)

    def _with(self, action: Callable[[ResultT], ValueT], *args, **kwargs) -> Self:
        return self._of(self._actions |then>> action, *args, **kwargs)

    @_invalid_when(_method_calling_preparation)
    def _like_operation(
        self,
        operation: merger_of[Any],
        value: Special[Self | Ellipsis],
        *,
        is_inverted: bool = False
    ) -> Self:
        second_branch_of_operation = (
            value._callable()
            if isinstance(value, _LambdaGenerator)
            else (taken(value) if value is not Ellipsis else value)
        )

        is_becoming_template = self._is_template or value._is_template

        first, second = (
            (self._callable(), second_branch_of_operation)
            if not is_inverted
            else (second_branch_of_operation, self._callable())
        )

        return self._of(
            taken |then>> templately(mergely, taken(operation), first, second)
            if value is Ellipsis
            else mergely(taken(operation), first, second)
        )

    def _callable(self) -> Self:
        return self._of(ActionChain([returned])) if len(self._actions) == 0 else self

    @_invalid_when(_method_calling_preparation)
    def __call__(self, *args, **kwargs) -> Self | ResultT:
        return (
            (
                self._with(right_partial(call, *args, **kwargs))
                if (
                    len(self._actions) == 0
                    or self._last_action_nature.value is _forced_call
                )
                else (self._actions)(*args, **kwargs)
            )
            if Ellipsis not in (*args, *kwargs.values())
            else self._with(right_partial(templately, *args, **kwargs))
        )

    def __getattr__(self, attribute_name: str) -> Self:
        return self._with(
            getattr |by| attribute_name,
            last_action_nature=contextual(attribute_name, when=_attribute_getting),
        )

    @_invalid_when(_method_calling_preparation)
    def __getitem__(self, key: Any) -> Self:
        return self._with(
            itemgetter(key),
            last_action_nature=contextual(key, when=_item_getting),
        )

    def __with_setting(self, setting: Callable[[Any, Any, Any], Any], value: Any) -> Self:
        return self._of(
            self._actions[:-1]
            |then>> right_partial(setting, self.last_action_nature.context, value)
        )

    def __pos__(self) -> Self:
        return self._with(pos)

    def __neg__(self) -> Self:
        return self._with(neg)

    def __invert__(self) -> Self:
        return self._with(invert)

    def __gt__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(gt, value)

    def __ge__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(ge, value)

    def __lt__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(lt, value)

    def __le__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(le, value)

    def __eq__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(eq, value)

    def __ne__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(ne, value)

    def __add__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(add, value)

    def __sub__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(sub, value)

    def __mul__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(mul, value)

    def __floordiv__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(floordiv, value)

    def __truediv__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(truediv, value)

    def __mod__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(mod, value)

    def __pow__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(pow, value)

    def __or__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(or_, value)

    def __and__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(and_, value)

    def __lshift__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(lshift, value)

    def __radd__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(add, value, is_inverted=True)

    def __rsub__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(sub, value, is_inverted=True)

    def __rmul__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(mul, value, is_inverted=True)

    def __rfloordiv__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(floordiv, value, is_inverted=True)

    def __rtruediv__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(truediv, value, is_inverted=True)

    def __rmod__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(mod, value, is_inverted=True)

    def __rpow__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(pow, value, is_inverted=True)

    def __ror__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(or_, value, is_inverted=True)

    def __rand__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(and_, value, is_inverted=True)

    def __rshift__(self, value: Special[Self | Ellipsis]) -> Self:
        return self._like_operation(lshift, value, is_inverted=True)


def not_(generator: _LambdaGenerator) -> LambdaGeneratingError:
    return generator._not()


x = _LambdaGenerator('x')