__all__ = (
    "PyhandingError", "NeutralActionChainError", "TemplatedActionChainError"
)


class PyhandingError(Exception):
    pass


class NeutralActionChainError(PyhandingError):
    pass


class TemplatedActionChainError(PyhandingError):
    __notes__ = ["Regular chain should not contain Ellipsis"]