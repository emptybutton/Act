__all__ = (
    "PyhandingError",
    "ReturningError",
    "InvalidInitializationError",
    "AtomizationError",
    "TemplatedActionChainError",
    "LambdaGeneratorError",
    "LambdaGeneratingError",
    "LambdaSettingError",   
)


class PyhandingError(Exception): ...


class FlagError(PyhandingError): ...


class ReturningError(PyhandingError): ...


class InvalidInitializationError(PyhandingError): ...


class AtomizationError(PyhandingError): ...


class ActionChainError(PyhandingError): ...


class TemplatedActionChainError(ActionChainError):
    __notes__ = ["Regular chain should not contain Ellipsis"]


class LambdaGeneratorError(PyhandingError): ...


class LambdaGeneratingError(LambdaGeneratorError): ...


class LambdaSettingError(LambdaGeneratorError):
    __notes__ = ["It is possible to set only after getting an attribute or item"]