import grpc


def validate_less_than(
    n: int,
    less_than: int,
    code: grpc.StatusCode,
    message: str,
    context: grpc.ServicerContext,
):
    """Validates that a number is less than a specified threshold.

    This function checks if the given number 'n' is less than the specified
    threshold 'less_than'. If the condition is not met (i.e., n >= less_than),
    the function aborts the gRPC call using the provided context, status code,
    and error message.

    Args:
        n: The number to validate.
        less_than: The threshold value that n should be less than.
        code: The gRPC status code to use if validation fails.
        message: The error message to include in the gRPC response if validation fails.
        context: The gRPC service context for the current call.

    Returns:
        None. If the validation fails, the function aborts the gRPC call and does not return.

    Example:
        >>> validate_less_than(5, 10, grpc.StatusCode.INVALID_ARGUMENT,
        ...                    'Value must be less than 10', context)
        # No error, continues execution

        >>> validate_less_than(15, 10, grpc.StatusCode.INVALID_ARGUMENT,
        ...                    'Value must be less than 10', context)
        # Aborts with INVALID_ARGUMENT and the provided message
    """

    if n >= less_than:
        context.abort(code=code, details=message)
