from unittest.mock import Mock

from py_micro.service.validators import common


def test_validate_less_than_actually_is():
    """
    Test case to verify that `common.validate_less_than` behaves correctly
    when the 'value' is indeed less than 'other'.

    This test expects no exceptions or context abortions to occur, indicating
    that the validation passes successfully when the condition is met.
    """
    common.validate_less_than(1, 2, None, "", None)


def test_validate_less_than_actually_equal():
    """
    Test case to verify that `common.validate_less_than` correctly
    identifies when 'value' is equal to 'other' and aborts the context.

    It mocks the context to assert that `context.abort` is called exactly once,
    signifying that the validation fails as expected when the values are equal.
    """
    context = Mock()

    common.validate_less_than(1, 1, None, "", context)

    context.abort.assert_called_once()


def test_validate_less_than_actually_more():
    """
    Test case to verify that `common.validate_less_than` correctly
    identifies when 'value' is greater than 'other' and aborts the context.

    It mocks the context to assert that `context.abort` is called exactly once,
    signifying that the validation fails as expected when the 'value'
    is not less than 'other'.
    """
    context = Mock()

    common.validate_less_than(2, 1, None, "", context)

    context.abort.assert_called_once()
