"""Exposes the default converter for this package"""

from __future__ import annotations

from typing import TypeAlias

from beartype.typing import Annotated, Any, Literal, get_args, get_origin
from cattrs.converters import Converter

from type_cellar.deduping import register_dedupe_hooks

from .. import SentinelMeta
from ..converters.attrs_converters import register_attrs_hooks
from .datetimes import register_datetime_hooks
from .enums import register_enum_hooks
from .exceptions import register_exception_hooks
from .json_ import (
    register_json_hooks,
)
from .sentinels import register_sentinel_hooks
from .uuid_hooks import register_uuid_hooks

DropStrategy: TypeAlias = Literal["drop_none", "replace_none_null"]  # noqa: F821


class ModelConverter(Converter):
    """Exposes different options for destructuring `None` in the same `Converter` object"""

    def drop_none(self, obj: Any, destruct: bool = True) -> dict[str, str]:
        """Remove all remaining `None`"""
        des = self.unstructure(obj) if destruct else obj
        return {k: v for k, v in des.items() if v is not None}

    def replace_none_null(self, obj: Any, destruct: bool = True) -> dict[str, str]:
        """Replace any remaining `None` with 'null'"""
        des = self.unstructure(obj) if destruct else obj
        return {k: ("null" if v is None else v) for k, v in des.items()}

    def serialize_attributes(
        self,
        obj: Any,
        destruct: bool = True,
        strategy: DropStrategy = "drop_none",
    ) -> dict[str, str]:
        """
        Wraps the converter's normal operations with another conversion of `None`.

        NOTE: This assumes the converter has handled all conversions of other values to `str`. Test these conversions robustly for every model used.
        """
        if strategy == "drop_none":
            return self.drop_none(obj, destruct)
        return self.replace_none_null(obj, destruct)


def optional_string_structure_hook(
    value: str | None, _: type[str | None]
) -> str | None:
    """Reconstruct strings which were converted to a placeholder for `None`"""
    if isinstance(value, str):
        if value.lower() == "null" or value.strip() == "" or value == "omitted":
            return None
        return value
    if value is None:
        return None


def get_converter() -> ModelConverter:
    converter = ModelConverter()
    register_uuid_hooks(converter)
    register_datetime_hooks(converter)
    register_enum_hooks(converter)
    register_exception_hooks(converter)
    register_json_hooks(converter)
    register_sentinel_hooks(converter)
    register_attrs_hooks(converter)
    register_dedupe_hooks(converter)

    # Final hooks
    converter.register_structure_hook(str | None, optional_string_structure_hook)

    def _annotated_structure_unwrap(v, t):
        inner = get_args(t)[0]
        return converter.structure(v, inner)

    converter.register_structure_hook_func(
        lambda t: get_origin(t) is Annotated, _annotated_structure_unwrap
    )

    @converter.register_unstructure_hook
    def _unstructure_type_hook(v: type):
        """Last catch-all hook"""
        try:
            if issubclass(v, SentinelMeta):
                return v.value()
            elif issubclass(v, BaseException):
                return v.__name__
            elif isinstance(v, str) and v.lower() == "null":
                return None
        except TypeError:
            pass
        return v

    # TODO: Recursive hooks
    # _ = converter.register_unstructure_hook_factory(
    #     attr.has,
    #     get_unstructure_attrs_factory(converter),  # our factory
    # )
    # _ = converter.register_structure_hook_factory(
    #     attr.has, get_structure_attrs_factory(converter)
    # )

    return converter
