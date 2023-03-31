__all__ = (
    "PyhandingError",
    "NeutralActionChainError",
    "TemplatedActionChainError",
    "LambdaGeneratorError",
    "LambdaGeneratingError",
    "LambdaSettingError",   
)


class PyhandingError(Exception):
    pass


class ActionChainError(PyhandingError):
    pass


class NeutralActionChainError(ActionChainError):
    pass


class TemplatedActionChainError(ActionChainError):
    __notes__ = ["Regular chain should not contain Ellipsis"]


class LambdaGeneratorError(PyhandingError):
    pass


class LambdaGeneratingError(LambdaGeneratorError):
    pass


class LambdaSettingError(LambdaGeneratorError):
    __notes__ = ["It is possible to set only after getting an attribute or item"]