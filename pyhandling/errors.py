class PyhandingError(Exception):
    pass


class HandlingRecursionError(PyhandingError):
    pass


class HandlingRecursionDepthError(HandlingRecursionError):
    __notes__ = ("To change the limit, call recursive with the max_recursion_depth argument, with the desired value", )