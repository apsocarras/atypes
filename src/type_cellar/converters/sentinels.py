from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, TypeVar

from cattrs import Converter

from .._types import (
    SentinelMeta,
)
from ._raise_util import raise_type_error


def sentinel_des_hook_factory(cls: type) -> Callable[..., str]:
    return lambda v: str(v)  # pyright: ignore[reportUnknownVariableType]


def sentinel_optional_des_hook_factory(cls: type) -> Callable[..., str | None]:
    return lambda v: str(v) if v is not None else None  # pyright: ignore[reportUnknownVariableType]


_T_Sentinel = TypeVar("_T_Sentinel", bound=SentinelMeta)


def sentinel_res_hook_factory(cls: type[_T_Sentinel]) -> Callable[..., _T_Sentinel]:
    def _wrapper(value: Any, _: type[_T_Sentinel]) -> _T_Sentinel:
        if isinstance(value, str) and value == cls.value():
            return cls.make()
        elif isinstance(value, cls):
            return value
        else:
            raise_type_error(value, cls)

    return _wrapper


def sentinel_optional_res_hook_factory(
    cls: type[_T_Sentinel],
) -> Callable[..., _T_Sentinel | None]:
    def _wrapper(value: Any, _: type[_T_Sentinel] | None) -> _T_Sentinel | None:
        if isinstance(value, str):
            if value == cls.value():
                return cls.make()
            elif value == "null" or value == "none":
                return None
        elif isinstance(value, cls):
            return value
        elif value is None:
            return None
        raise_type_error(value, cls)

    return _wrapper


## SENTINEL UNION TYPES ##
# TODO: Can these be caught under an umbrella union type with the above?


def register_sentinel_hooks(conv: Converter) -> None:
    """
    >>> import cattrs
    >>> from typing_extensions import override, Literal
    >>> conv = cattrs.Converter()
    >>> register_sentinel_hooks(conv)

    # --- unstructure via sentinel factory ---

    >>> class DummySentinel(SentinelMeta):
    ...     @override
    ...     def __str__(self):
    ...         return self.value()
    ...
    ...     @staticmethod
    ...     @override
    ...     def value() -> str:
    ...         return "DUMMY"
    ...
    ...     @override
    ...     def __bool__(self) -> Literal[False]:
    ...         return False

    >>> conv.unstructure(DummySentinel())
    'DUMMY'

    # --- NotImplementSentinel ---
    >>> conv.structure(None, NotImplementSentinel) is None
    True
    >>> conv.structure("null", NotImplementSentinel) is None
    True
    >>> conv.structure(
    ...     NotImplementSentinel.value(), NotImplementSentinel
    ... ) is NOT_IMPLEMENTED
    True
    >>> conv.structure(NotImplementSentinel(), NotImplementSentinel) is NOT_IMPLEMENTED
    True
    >>> conv.structure(NotImplementSentinel, NotImplementSentinel) is NOT_IMPLEMENTED
    True

    # --- OmittedDefaultSentinel ---
    >>> conv.structure(
    ...     OmittedDefaultSentinel.value(), OmittedDefaultSentinel
    ... ) is OMITTED_DEFAULT
    True

    # --- OptionalClientId ---
    >>> conv.structure(None, OptionalClientId) is None
    True
    >>> conv.structure("null", OptionalClientId) is None
    True
    >>> conv.structure("abc123", OptionalClientId)
    'abc123'
    >>> conv.structure(
    ...     NotImplementSentinel.value(), OptionalClientId
    ... ) is NOT_IMPLEMENTED
    True
    >>> conv.structure(NotImplementSentinel(), OptionalClientId) is NOT_IMPLEMENTED
    True
    >>> conv.structure(NotImplementSentinel, OptionalClientId) is NOT_IMPLEMENTED
    True

    # --- OmittedDefaultSentinel | str ---
    >>> conv.structure(
    ...     OmittedDefaultSentinel.value(), OmittedDefaultSentinel | str
    ... ) is OMITTED_DEFAULT
    True
    >>> conv.structure("some-id", OmittedDefaultSentinel | str)
    'some-id'
    """
    pred: Callable[..., bool] = lambda t: issubclass(t, SentinelMeta)

    def _reg(des_or_res: Literal["des", "res"], hook: Callable[..., Any]) -> None:
        nonlocal conv, pred
        if des_or_res == "des":
            _ = conv.register_unstructure_hook_factory(pred, hook)
        else:
            _ = conv.register_structure_hook_factory(pred, hook)

    _reg("des", sentinel_des_hook_factory)
    _reg("des", sentinel_optional_des_hook_factory)
    _reg("res", sentinel_res_hook_factory)
    _reg("res", sentinel_optional_res_hook_factory)
