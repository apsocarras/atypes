import cattrs

from type_cellar.converters._raise_util import raise_type_error


def des_exception_instance(exc: BaseException) -> str:
    return repr(exc)


def des_exception_type(t: type) -> str:
    if issubclass(t, BaseException):
        return t.__name__
    raise_type_error(t, "BaseException")


def register_exception_hooks(conv: cattrs.Converter) -> None:
    """
    >>> import cattrs
    >>> conv = cattrs.Converter()
    >>> register_exception_hooks(conv)

    # Instances
    >>> conv.unstructure(GeneratorExit())
    'GeneratorExit()'
    >>> conv.unstructure(ValueError("bad"))
    "ValueError('bad')"

    # Classes
    >>> conv.unstructure(GeneratorExit)
    'GeneratorExit'
    >>> conv.unstructure(ValueError)
    'ValueError'

    # Structuring union
    >>> conv.structure(None, OptionalErrorReturnOrStr) is None
    True
    >>> conv.structure("oops", OptionalErrorReturnOrStr)
    'oops'
    >>> conv.structure(ValueError("bad"), OptionalErrorReturnOrStr)
    'bad'
    >>> conv.structure(GeneratorExit, OptionalErrorReturnOrStr)
    'GeneratorExit'
    """
    # Single hook for all exception instances, including GeneratorExit/SystemExit/etc.
    conv.register_unstructure_hook(BaseException, des_exception_instance)

    # Handle exception classes (e.g., ValueError, GeneratorExit) appearing as values
    conv.register_unstructure_hook(type, des_exception_type)
