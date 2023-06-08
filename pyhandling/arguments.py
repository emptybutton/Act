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

from pyhandling.annotations import A, D
from pyhandling.atoming import atomically
from pyhandling.errors import ArgumentError
from pyhandling.signature_assignmenting import (
    Decorator, call_signature_of
)
from pyhandling.structure_management import (
    without, frozendict, flat, tmap, without_duplicates,
    reversed_table
)
from pyhandling.tools import action_repr_of


__all__ = ("ArgumentKey", "Arguments", "as_arguments", "unpackly")


_EMPTY_DEFAULT_VALUE: Final[object] = object()

_ArgumentKeyT = TypeVar("_ArgumentKeyT", bound=int | str)


@dataclass(frozen=True, repr=False)
class ArgumentKey(Generic[_ArgumentKeyT, D]):
    """
    Data class for structuring getting value from `Arguments` via `[]`.
    """

    value: _ArgumentKeyT
    is_keyword: bool = field(default=False, kw_only=True)
    default: D = field(
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
            action_repr_of(self.value)
            if with_position or self.is_keyword
            else '...'
        )

        formatted_value = (
            '...'
            if self.default is _EMPTY_DEFAULT_VALUE
            else action_repr_of(self.default)
        )

        return (
            f"{formatted_key}={formatted_value}"
            if self.is_keyword
            else formatted_key
        )


class ArgumentKeys:
    """
    Iterable descriptor class storing and sorting `ArgumentKey`s.

    Sorts keys by their keyword in `positional` and `keywords` accordingly.

    Can be used as a `keys` method in `Mapping` objects.
    To do this, it returns the values of its keys when called.

    In cases of use other than as a descriptor, the call is less justified.
    """

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


class Arguments(Mapping, Generic[A]):
    """
    Data class for structuring the storage of any arguments.

    Sorts arguments into `args` and `kwargs` properties.

    With `*` unpacking, unpacks only positional arguments, with `**` only
    keywords.

    By `in` checks for argument values.

    Searches for an argument value by an `ArgumentKey` passed via `[]`.
    """

    def __init__(
        self,
        args: Iterable[A] = tuple(),
        kwargs: Optional[Mapping[str, A]] = None,
    ):
        self._args = tuple(args)
        self._kwargs = frozendict(
            kwargs if kwargs is not None else dict()
        )

    @property
    def args(self) -> Tuple[A]:
        return self._args

    @property
    def kwargs(self) -> frozendict[str, A]:
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
        return "({}{}{})".format(
            ', '.join(map(str, self.args)),
            (
                ', ' if self.args and self.kwargs else str()
            ),
            ', '.join(map(
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

    def __getitem__(self, key: ArgumentKey | int | str) -> A:
        if isinstance(key, int | str):
            key = ArgumentKey(key, is_keyword=isinstance(key, str))

        return (
            (self.kwargs if key.is_keyword else self.args)[key.value]
            if key in self.keys or key.default is _EMPTY_DEFAULT_VALUE
            else key.default
        )

    def __iter__(self) -> Iterator[A]:
        return iter(self.args)

    def __len__(self) -> int:
        return len(self.keys)

    def __contains__(self, value: A) -> bool:
        return value in self.args or value in self.kwargs.values()

    def expanded_with(self, *args: Special[Self], **kwargs: Any) -> Self:
        """Method to create another pack with input arguments."""

        args = flat(
            arg.args if isinstance(arg, Arguments) else (arg, ) for arg in args
        )

        return self.__class__(
            (*self.args, *args),
            self.kwargs | kwargs
        )

    def only_with(self, *arguments_or_keys: A | ArgumentKey) -> Self:
        """Method for cloning with values obtained from input keys."""

        keys = tmap(self._as_key, without_duplicates(arguments_or_keys))
        keyword_keys = ArgumentKeys(keys).keywords

        return type(self)(
            tuple(self[key] for key in without(keys, keyword_keys)),
            {keyword_key.value: self[keyword_key] for keyword_key in keyword_keys},
        )

    def without(self, *arguments_or_keys: A | ArgumentKey) -> Self:
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
        """Method for creating arguments with this method's input arguments."""

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
    When passed a single positional `Arguments`, it returns it.
    """

    if len(args) == 1 and isinstance(args[0], Arguments) and not kwargs:
        return args[0]

    return Arguments(args, kwargs)


@atomically
class unpackly(Decorator):
    """Decorator to unpack input arguments into an input action."""

    def __call__(self, arguments: Special[Arguments, Iterable]) -> Any:
        return (
            arguments.call(self._action)
            if isinstance(arguments, Arguments)
            else self._action(*arguments)
        )

    @cached_property
    def _force_signature(self) -> Signature:
        return call_signature_of(self).replace(return_annotation=(
            call_signature_of(self._action).return_annotation
        ))
