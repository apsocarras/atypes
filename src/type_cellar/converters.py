"""``cattrs`` hooks for deconstructing/reconstructing types"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, TypeAlias, TypeVar

import attr
import attrs
import cattrs
from cattrs.gen import make_dict_unstructure_fn

from . import (  # pyright: ignore[reportPrivateUsage]
    _OMITTED_DEFAULT,
    OmittedDefaultSentinel,
    _nobeartype,
)

DictDesFunc: TypeAlias = Callable[[Any], dict[str, Any]]


def omit_des(
    cls: type,
    conv: cattrs.Converter,
    dict_des_fn: DictDesFunc | OmittedDefaultSentinel = _OMITTED_DEFAULT,
) -> Callable[..., dict[str, Any]]:
    """Omit fields in an attrs.AttrsInstance if field metadata says to"""
    fn: DictDesFunc = dict_des_fn or make_dict_unstructure_fn(
        cls,
        conv,  # _cattrs_omit_if_default=omit_if_default # using custom metadata override
    )

    @_nobeartype
    def wrapped(
        inst: Annotated[
            attrs.AttrsInstance,
            "`attrs.AttrsInstance` is an empty protocol and not a real runtime type.",
        ],
    ) -> dict[str, Any]:
        d = fn(inst)
        return {
            k: v
            for k, v in d.items()
            if attr.has(cls := inst.__class__)
            and not attr.fields_dict(cls)[k].metadata.get("omit", False)
        }

    return wrapped


_T = TypeVar("_T", bound=attrs.AttrsInstance)
