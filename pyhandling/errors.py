__all__ = (
    "PyhandingError", "NeutralActionChainError", "HandlingRecursionError",
    "HandlingRecursionDepthError"
)


class PyhandingError(Exception):
    pass


class NeutralActionChainError(PyhandingError):
    pass