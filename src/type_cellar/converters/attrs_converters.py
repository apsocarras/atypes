"""Generic ``cattrs`` converters for attrs types"""

# pyright: reportPrivateUsage = false
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Annotated, Any, TypeAlias

import attr
import attrs
import cattrs
from cattrs.gen import make_dict_structure_fn, make_dict_unstructure_fn

DictDesFunc: TypeAlias = Callable[[Any], dict[str, Any]]
AttrsInstance: TypeAlias = Annotated[
    attrs.AttrsInstance,
    "`attrs.AttrsInstance` is an empty protocol and not a real runtime type.",
]


def _iter_by_metadata(cls: type) -> Iterable[Any]:
    if not attr.has(cls):
        raise TypeError(f"{cls} is not an attrs class")
    for f in attrs.fields(cls):
        if f.metadata.get("omit", False) or (
            f.metadata.get("omit_if_default", False) and f.value == attr.NOTHING
        ):
            continue
        yield f


def des_omit_factory(
    obj: AttrsInstance,
    conv: cattrs.Converter,
) -> Callable[..., dict[str, Any]]:
    """Omit fields in an attrs.AttrsInstance if field metadata says to

    ```pycon
    >>> import attr
    >>> import cattrs
    >>> @attr.define
    >>> class Foo:
        ... bar: str = attr.field(default="bar", metadata={"omit": True})
        ... baz: str = attr.field(default="baz")

    >>> conv = cattrs.Converter()
    >>> conv.register_unstructure_hook(Foo, omit_des(Foo, conv))
    >>> f = Foo()
    >>> conv.unstructure(f)
    {'baz': 'baz'}

    ```
    """

    return lambda: {
        f.name: conv.unstructure(getattr(obj, f.name))
        for f in _iter_by_metadata(obj.__class__)
    }


def skip_attrs_factory(
    cls: type[Any], c: cattrs.Converter, *args: str
) -> Callable[[Any], dict[str, Any]]:
    """
    Skip named attributes when unstructuring.
    WARNING: Be sure class has actual attributes if using attr.s (attr.s(auto_attribs=True))

    ```pycon
    >>> from cattrs import Converter
    >>> import attr
    >>> c = Converter()

    >>> @attr.s(auto_attribs=True)
    ... class MyMessage:
    ...     msg: dict[str, Any]
    ...     foo: str
    ...     keep: str
    ...     @classmethod
    ...     def field_names(cls):
    ...         return
    >>> unst_hook = skip_attrs_factory(MyMessage, c, "msg", "foo")
    >>> c.register_unstructure_hook(MyMessage, unst_hook)
    >>> c.unstructure(MyMessage(msg={"Drink your": "Ovaltine"}, foo="bar", keep="I'm safe"))
    {'keep': "I'm safe"}

    ```
    """
    cls_fields: dict[str, attr.Attribute[Any]] = attrs.fields_dict(cls)
    cmds = {}
    for a in args:
        if a not in cls_fields:
            raise AttributeError(name=a, obj=cls)

        cmds[a] = cattrs.override(omit=True)

    return make_dict_unstructure_fn(
        cls,
        c,
        **cmds,  # type: ignore
    )


def register_attrs_hooks(
    conv: cattrs.Converter,
    *classes: type,
) -> None:
    """Register default hooks for an `attrs.AttrsInstance`: `omit_des` and `make_dict_structure_fn`"""
    for cls in classes:
        conv.register_unstructure_hook(cls, des_omit_factory(cls, conv))
        conv.register_structure_hook(cls, make_dict_structure_fn(cls, conv))
