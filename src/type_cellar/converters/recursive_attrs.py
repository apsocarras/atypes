from collections.abc import Callable

import attr
from beartype.typing import Any
from cattrs import Converter


def get_unstructure_attrs_factory(
    converter: Converter,
) -> Callable[..., Callable[..., dict[Any, Any]]]:
    """1. Call on a converter to produce a factorty 2. Register the factory"""

    def unstructure_attrs_factory(
        cls: type[Any],
    ) -> Callable[..., dict[Any, Any]]:
        """
        Returns a function that converts an instance of a given attrs object into a dict
        """

        def _unstructure_attrs(obj: Any) -> dict[Any, Any]:
            result: dict[Any, Any] = {}
            for field in attr.fields(cls):
                value = getattr(obj, field.name)
                result[field.name] = converter.unstructure(value)
            return result

        return _unstructure_attrs

    return unstructure_attrs_factory


def get_structure_attrs_factory(
    converter: Converter,
) -> Callable[..., Callable[..., Any]]:
    """1. Call on a converter to produce a factorty 2. Register the factory"""

    def structure_attrs_factory(cls: type[Any]):
        """ChatGPT - test/audit"""
        fields = attr.fields(cls)

        def _structure(obj: Any, _: Any) -> Any:
            # If it's already an instance, return as-is.
            if isinstance(obj, cls):
                return obj
            if obj is None:
                return None
            if not isinstance(obj, dict):
                # Let cattrs handle non-dict inputs (e.g., wrong type)
                return converter.structure(obj, cls)

            vals = {}
            for f in fields:
                if f.name in obj:
                    typ = f.type  # may be typing.Any / optional / containers
                    if typ is None:
                        # No type info; pass value through
                        vals[f.name] = obj[f.name]
                    else:
                        vals[f.name] = converter.structure(obj[f.name], typ)
                # else: omit, so attrs can apply default/factory if present
            return cls(**vals)

        return _structure

    return structure_attrs_factory
