from collections import OrderedDict
from functools import cached_property, partial
from dataclasses import dataclass, field
from inspect import Signature
from operator import attrgetter
from typing import (
    Final, Generic, Iterable, Optional, Tuple, Self, Any, Callable, TypeVar,
    Iterator, Mapping
)

from pyannotating import Special

from pyhandling.annotations import ValueT
from pyhandling.atoming import atomically
from pyhandling.data_flow import to
from pyhandling.signature_assignmenting import (
    Decorator, call_signature_of
)
from pyhandling.structure_management import (
    without, frozendict, with_opened_items, tmap, without_duplicates,
    reversed_table
)


__all__ = ("ArgumentKey", "Arguments", "as_arguments", "unpackly")


_EMPTY_DEFAULT_VALUE: Final[object] = object()

_ArgumentKeyT = TypeVar("_ArgumentKeyT", bound=int | str)


@dataclass(frozen=True, repr=False)
class ArgumentKey(Generic[_ArgumentKeyT, ValueT]):
    """
    Data class for structuring getting value from `Arguments` via `[]`.
    """

    value: _ArgumentKeyT
    is_keyword: bool = field(default=False, kw_only=True)
    default: ValueT = field(
        default_factory=lambda: _EMPTY_DEFAULT_VALUE,
        compare=False,
        kw_only=True,
    )

    def __post_init__(self) -> None:
        if (
            isinstance(self.value, int) and self.is_keyword
            or isinstance(self.value, str) and not self.is_keyword
        ):
            raise ArgumentError("keyword ArgumentKey value must be a string")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)})"

    def __str__(self, *, with_position: bool = True) -> str:
        formatted_key = (
            str(self.value) if with_position or self.is_keyword else '...'
        )

        formatted_value = (
            '...' if self.default is _EMPTY_DEFAULT_VALUE else str(self.default)
        )

        return (
            f"{formatted_key}={formatted_value}"
            if self.is_keyword
            else formatted_key
        )


class ArgumentKeys:
    def __init__(self, keys: Iterable[ArgumentKey]):
        self._keys = tuple(keys)

    @cached_property
    def keywords(self) -> Tuple[ArgumentKey[str, Any]]:
        return tuple(OrderedDict.fromkeys(filter(
            lambda key: key.is_keyword,
            self._keys
        )).keys())

    @cached_property
    def positional(self) -> Tuple[ArgumentKey[int, Any]]:
        return without(self._keys, self.keywords)

    def __repr__(self) -> str:
        return f"ArgumentKeys({str(self)})"

    def __str__(self) -> str:
        return "({})".format(', '.join(map(
            partial(ArgumentKey.__str__, with_position=False),
            self._keys,
        )))

    def __iter__(self) -> Iterator[ArgumentKey]:
        return iter(self._keys)

    def __call__(self) -> Tuple[int | str]:
        return tmap(attrgetter("value"), self._keys)


class Arguments(Mapping, Generic[ValueT]):
    """
    Data class for structuring the storage of any arguments.

    Has the ability to get an attribute when passed to `[]` `ArgumentKey`
    instance.
    """

    def __init__(
        self,
        args: Iterable[ValueT] = tuple(),
        kwargs: Optional[Mapping[str, ValueT]] = None,
    ):
        self._args = tuple(args)
        self._kwargs = frozendict(
            kwargs if kwargs is not None else dict()
        )

    @property
    def args(self) -> Tuple[ValueT]:
        return self._args

    @property
    def kwargs(self) -> frozendict[str, ValueT]:
        return self._kwargs

    @cached_property
    def keys(self) -> ArgumentKeys:
        return ArgumentKeys((
            *map(ArgumentKey, range(len(self.args))),
            *(
                ArgumentKey(key, default=value, is_keyword=True)
                for key, value in self.kwargs.items()
            ),
        ))

    def __repr__(self) -> str:
        return f"{type(self).__name__}{str(self)}"

    def __str__(self) -> str:
        return "({formatted_args}{argument_separation_part}{formatted_kwargs})".format(
            formatted_args=', '.join(map(str, self.args)),
            argument_separation_part=(
                ', ' if self.args and self.kwargs else str()
            ),
            formatted_kwargs=', '.join(map(
                lambda item: f"{item[0]}={item[1]}",
                self.kwargs.items())
            ),
        )


    def __eq__(self, other: Special[Self]) -> bool:
        return (
            isinstance(other, Arguments)
            and self.args == other.args
            and self.kwargs == other.kwargs
        )

    def __getitem__(self, key: ArgumentKey | int | str) -> ValueT:
        if isinstance(key, int | str):
            key = ArgumentKey(key, is_keyword=isinstance(key, str))

        return (
            (self.kwargs if key.is_keyword else self.args)[key.value]
            if key in self.keys or key.default is _EMPTY_DEFAULT_VALUE
            else key.default
        )

    def __iter__(self) -> Iterator[ValueT]:
        return iter((*self.args, *self.kwargs.keys()))

    def __len__(self) -> int:
        return len(self.keys)

    def __or__(self, other: Self) -> Self:
        return self.merge_with(other)

    def __contains__(self, value: ValueT) -> bool:
        return value in tuple(self)

    def expanded_with(self, *args: Special[Self], **kwargs: Any) -> Self:
        """Method to create another pack with input arguments."""

        args = with_opened_items(
            arg.args if isinstance(arg, Arguments) else (arg, ) for arg in args
        )

        kwargs
        OrderedDict(key: value for key, value in kwargs.items() if )

        return self.__class__(
            (*self.args, *args),
            self.kwargs | kwargs
        )

    def only_with(self, *arguments_or_keys: ValueT | ArgumentKey) -> Self:
        """Method for cloning with values obtained from input keys."""

        keys = tmap(self._as_key, without_duplicates(arguments_or_keys))
        keyword_keys = ArgumentKeys(keys).keywords

        return type(self)(
            tuple(self[key] for key in without(keys, keyword_keys)),
            {keyword_key.value: self[keyword_key] for keyword_key in keyword_keys},
        )

    def without(self, *arguments_or_keys: ValueT | ArgumentKey) -> Self:
        """
        Method for cloning a pack excluding arguments whose keys are input to
        this method.
        """

        return self.only_with(*without(self.keys, arguments_or_keys))

    def call(self, caller: Callable) -> Any:
        """
        Method for calling an input function with arguments stored in an
        instance.
        """

        return caller(*self.args, **self.kwargs)

    @classmethod
    def of(cls, *args, **kwargs) -> Self:
        """Method for creating a pack with this method's input arguments."""

        return cls(args, kwargs)

    def _as_key(self, value: Any) -> ArgumentKey:
        if isinstance(value, ArgumentKey):
            return value

        try:
            key_of = partial(ArgumentKey, self.args.index(value))
        except ValueError:
            key_of = partial(ArgumentKey, reversed_table(self.kwargs)[value])

        return key_of(default=value)


def as_arguments(*args, **kwargs) -> Arguments:
    """
    Function to optionally convert input arguments into `Arguments`.
    When passed a single positional `Arguments` to the function, it returns it.
    """

    if len(args) == 1 and isinstance(args[0], Arguments) and not kwargs:
        return args[0]

    return Arguments(args, kwargs)


@atomically
class unpackly(Decorator):
    """Decorator to unpack the input `Arguments` into an input action."""

    def __call__(self, arguments: Arguments) -> Any:
        return arguments.call(self._action)

    @cached_property
    def _force_signature(self) -> Signature:
        return call_signature_of(self).replace(return_annotation=(
            call_signature_of(self._action).return_annotation
        ))
