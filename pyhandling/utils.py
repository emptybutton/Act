from collections import OrderedDict
from datetime import datetime
from functools import wraps, partial, cached_property, update_wrapper
from operator import itemgetter, call, not_, add, attrgetter, pos, neg, invert, gt, ge, lt, le, eq, ne, sub, mul, floordiv, truediv, mod, or_, and_, lshift
from typing import NamedTuple, Generic, Iterable, Tuple, Callable, Any, Mapping, Type, NoReturn, Optional, Self, TypeVar

from pyannotating import many_or_one, AnnotationTemplate, input_annotation, Special, method_of

from pyhandling.annotations import one_value_action, dirty, handler_of, ValueT, ContextT, ResultT, checker_of, ErrorT, action_for, merger_of, P, reformer_of, KeyT, MappedT
from pyhandling.arguments import ArgumentPack
from pyhandling.binders import returnly, closed, right_closed, right_partial, eventually, unpackly
from pyhandling.branchers import ActionChain, on, rollbackable, mergely, mapping_to_chain_of, mapping_to_chain, repeating
from pyhandling.language import then, by, to
from pyhandling.errors import LambdaGeneratingError
from pyhandling.flags import flag, nothing, Flag, flag_to
from pyhandling.synonyms import returned, raise_
from pyhandling.tools import documenting_by, in_collection, Clock, contextual, contextually, context_pointed


__all__ = (
    "atomically",
    "showly",
    "branching",
    "with_result",
    "shown",
    "binding_by",
    "taken",
    "as_collection",
    "yes",
    "no",
    "is_not",
    "map_",
    "zip_",
    "filter_",
    "value_map",
    "reversed_table",
    "templately",
    "value_map",
    "times",
    "with_error",
    "monadically",
    "mapping_to_chain_among",
    "execution_context_when",
    "saving_context",
    "bad",
    "maybe",
    "until_error",
    "writing",
    "reading",
    "considering_context",
    "right",
    "left",
    "either",
    "to_points",
    "to_acyclic_points",
    "x",
    "not_",
)


class atomically:
    """
    Decorator that removes the behavior of an input action, leaving only
    calling.
    """

    def __init__(self, action: action_for[ResultT]):
        self._action = action
        update_wrapper(self, self._action)

    def __repr__(self) -> str:
        return f"atomically({self._action})"

    def __call__(self, *args, **kwargs) -> ResultT:
        return self._action(*args, **kwargs)


class _Fork(NamedTuple, Generic[P, ResultT]):
    """NamedTuple to store an action to execute on a condition."""

    checker: Callable[P, bool]
    action: Callable[P, ResultT]


def branching(
    *forks: tuple[Callable[P, bool], Callable[P, ResultT]],
    else_: Callable[P, ResultT] = returned,
) -> Callable[P, ResultT]:
    """
    Function for using action branching like `if`, `elif` and `else` statements.

    With default `else_` takes actions of one value.
    """

    forks = map_(_Fork, forks)

    return (
        on(*forks[0], else_=else_)
        if len(forks) == 1
        else on(forks[0].checker, forks[0].action, else_=branching(*forks[1:]))
    )


def with_result(result: ResultT, action: Callable[P, Any]) -> Callable[P, ResultT]:
    """Function to force an input result for an input action."""

    return atomically(action |then>> taken(result))


shown: dirty[reformer_of[ValueT]]
shown = documenting_by("""Shortcut function for `returnly(print)`.""")(
    returnly(print)
)


def binding_by(template: Iterable[Callable | Ellipsis]) -> Callable[[Callable], ActionChain]:
    """
    Function to create a function by insertion its input function in the input
    template.

    The created function replaces `...` with an input action.
    """

    def insert_to_template(intercalary_action: Callable) -> ActionChain:
        """
        Function given as a result of calling `binding_by`. See `binding_by` for
        more info.
        """

        return ActionChain(
            intercalary_action if action is Ellipsis else action
            for action in template
        )

    return insert_to_template


taken: Callable[[ValueT], action_for[ValueT]] = documenting_by(
    """Shortcut function for `eventually(returned, ...)`."""
)(
    atomically(closed(returned) |then>> eventually)
)


as_collection: Callable[[many_or_one[ValueT]], Tuple[ValueT]]
as_collection = documenting_by(
    """
    Function to convert an input value into a tuple collection.
    With a non-iterable value, wraps it in a tuple.
    """
)(
    on(isinstance |by| Iterable, tuple, else_=in_collection)
)


yes: action_for[bool] = documenting_by("""Shortcut for `taken(True)`.""")(taken(True))
no: action_for[bool] = documenting_by("""Shortcut for `taken(False)`.""")(taken(False))


is_not: Callable[[handler_of[ValueT]], checker_of[ValueT]]
is_not = documenting_by("""Negation adding function.""")(
    binding_by(... |then>> not_)
)


map_ = documenting_by("""`map` function returning `tuple`""")(
    atomically(map |then>> tuple)
)


zip_ = documenting_by("""`zip` function returning `tuple`""")(
    atomically(zip |then>> tuple)
)


filter_ = documenting_by("""`filter` function returning `tuple`""")(
    atomically(filter |then>> tuple)
)


def value_map(
    mapped: Callable[[ValueT], MappedT],
    table: Mapping[KeyT, ValueT],
) -> OrderedDict[KeyT, MappedT]:
    return OrderedDict((_, mapped(value)) for _, value in table.items())


def reversed_table(table: Mapping[KeyT, ValueT]) -> OrderedDict[ValueT, KeyT]:
    return OrderedDict(map(reversed, table.items()))


def templately(action: action_for[ResultT], *args, **kwargs) -> Callable[[Any], ResultT]:
    return wraps(action)(lambda argument: action(
        *map(on(operation_by('is', Ellipsis), taken(argument)), args),
        **value_map(on(operation_by('is', Ellipsis), taken(argument)), kwargs),
    ))


times: Callable[[int], dirty[action_for[bool]]] = documenting_by(
    """
    Function to create a function that will return `True` the input value (for
    this function) number of times, then `False` once after the input count has
    passed, `True` again n times, and so on.

    Resulting function is independent of its input arguments.
    """
)(
    atomically(
        (add |by| 1)
        |then>> Clock
        |then>> closed(
            on(
                not_,
                returnly(lambda clock: (setattr |to| clock)(
                    "ticks_to_disability",
                    clock.initial_ticks_to_disability
                ))
            )
            |then>> returnly(lambda clock: (setattr |to| clock)(
                "ticks_to_disability",
                clock.ticks_to_disability - 1
            ))
            |then>> bool
        )
        |then>> eventually
    )
)


as_contextual: Callable[[ValueT | contextual[ValueT, Any]], contextual[ValueT, Any]]
as_contextual = documenting_by(
    """
    Function to represent an input value in `contextual` form if it is not
    already present.
    """
)(
    on(is_not(isinstance |by| contextual), contextual)
)


with_error: Callable[
    [Callable[P, ResultT]],
    Callable[P, contextual[Optional[ResultT], Optional[Exception]]]
]
with_error = documenting_by(
    """
    Decorator that causes the decorated function to return the error that
    occurred.

    Returns in `contextual` format (result, error).
    """
)(
    atomically(
        binding_by(... |then>> contextual)
        |then>> right_partial(rollbackable, contextual |to| nothing)
    )
)


monadically: Callable[
    [Callable[[one_value_action], reformer_of[ValueT]]],
    mapping_to_chain_of[reformer_of[ValueT]]
]
monadically = documenting_by(
    """
    Function for decorator to map actions of a certain sequence (or just one
    action) into a chain of transformations of a certain type.

    Maps actions by an input decorator one at a time.
    """
)(
    atomically(
        closed(map)
        |then>> binding_by(as_collection |then>> ... |then>> ActionChain)
        |then>> atomically
    )
)


mapping_to_chain_among = AnnotationTemplate(mapping_to_chain_of, [
    AnnotationTemplate(reformer_of, [input_annotation])
])


execution_context_when = AnnotationTemplate(mapping_to_chain_among, [
    AnnotationTemplate(contextual, [Any, input_annotation])
])


saving_context: execution_context_when[ContextT] = documenting_by(
    """Execution context without effect."""
)(
    monadically(lambda node: lambda root: contextual(
        node(root.value), when=root.context
    ))
)


bad = flag('bad', sign=False)


maybe: execution_context_when[Special[bad]]
maybe = documenting_by(
    """
    Execution context that stops the thread of execution When the `bad` flag
    returns.

    When stopped, returns the previous value calculated before the `bad` flag in
    context with `bad` flag.
    """
)(
    monadically(lambda node: lambda root: (
        root.value >= node |then>> on(
            eq |by| bad,
            taken(contextual(root.value, flag_to(root.context) | bad)),
            else_=contextual |by| root.context,
        )
        if root.context != bad
        else root
    ))
)


until_error: execution_context_when[Special[Exception | Flag[Exception]]]
until_error = documenting_by(
    """
    Execution context that stops the thread of execution when an error occurs.

    When skipping, it saves the last validly calculated value and an occurred
    error as context.
    """
)(
    monadically(lambda node: lambda root: (
        rollbackable(
            node |then>> (contextual |by| root.context),
            lambda error: contextual(root.value, when=flag_to(root.context, error)),
        )(root.value)
        if flag_to(root.context)[isinstance |by| Exception] == nothing
        else root
    ))
)


def showly(
    action_or_actions: many_or_one[one_value_action],
    *,
    show: dirty[one_value_action] = print,
) -> dirty[ActionChain]:
    """
    Executing context with the effect of writing results.
    Prints results by default.
    """

    return monadically(binding_by(... |then>> returnly(show)))(
        action_or_actions
    )


writing = flag("writing")
reading = flag("reading")


_ReadingResultT = TypeVar("_ReadingResultT")
_NewContextT = TypeVar("_NewContextT")


@documenting_by(
    """
    Execution context with the ability to read and write to a context.

    Writes to context by contextual node with `writing` context and reads value
    from context by contextual node with `reading` context.

    Before interacting with a context, the last calculated result must come to
    contextual nodes, after a context itself.

    When writing to a context, result of a contextual node will be a result
    calculated before it, and when reading, a result of reading.
    """
)
@monadically
@closed
def considering_context(
    node: Callable[[ValueT], ResultT] | contextually[
        Callable[[ValueT], Callable[[ContextT], _NewContextT]]
        | Callable[[ValueT], Callable[[ContextT], _ReadingResultT]],
        Special[writing | reading],
    ],
    root: contextual[ValueT, ContextT]
) -> contextual[ResultT | ValueT | _ReadingResultT, ContextT]:
    if isinstance(node, contextually):
        if node.context == writing:
            return contextual(root.value, node(root.value)(root.context))

        if node.context == reading:
            return contextual(node(root.value)(root.context), root.context)

    return saving_context(node)(root)


right = flag("right")
left = flag('left', sign=False)


def either(
    *context_and_action: tuple[ContextT, Callable[[contextual[ValueT, ContextT]], ResultT]],
    else_: Callable[[contextual[ValueT, ContextT]], ResultT] = returned,
) -> Callable[[contextual[ValueT, ContextT]], ResultT]:
    """Shortcut for `branching` with context checks."""

    return branching(*(
        (lambda root: root.context is context, action)
        for context, action in context_and_action
    ))



to_points: mapping_to_chain_among[Flag] = documenting_by(
    """Execution context of flag `points`."""
)(
    monadically(lambda action: lambda flags: flag_to(*map(
        attrgetter("point") |then>> action,
        flags,
    )))
)


to_acyclic_points: mapping_to_chain_among[Flag] = documenting_by(
    """
    Flag `point` execution context of flags whose `points` do not point to
    themselves.
    """
)(
    monadically(on |to| is_not(isinstance |by| Flag)) |then>> to_points
)


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

    def is_not(self, value: Any) -> Self:
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