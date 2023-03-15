__all__ = (
    "PyhandingError", "NeutralActionChainError"
)


class PyhandingError(Exception):
    pass


class NeutralActionChainError(PyhandingError):
    pass