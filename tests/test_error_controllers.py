@mark.parametrize(
    "error_storage, result_errors",
    [
        (ZeroDivisionError(), (ZeroDivisionError(), )),
        (MockObject(error=TypeError()), (TypeError(), )),
        (
            MockObject(errors=(
                TypeError(),
                AttributeError(),
                MockObject(error=ZeroDivisionError())
            )),
            (TypeError(), AttributeError(), ZeroDivisionError())
        ), 

    ]
)
def test_errors_from(error_storage: error_storage_of[Exception], result_error_types: Iterable[Type[Exception]]):
    result_errors = errors_from(error_storage)
    
    assert len(result_errors) == len(result_error_types)
    assert all(map(
        lambda error, error_type: type(error) is error_type,
        result_errors,
        result_error_types)
    )
