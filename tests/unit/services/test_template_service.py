from unittest.mock import patch
import pytest

from py_micro.model.template_service_pb2 import HealthCheckRequest, HealthCheckResponse
from py_micro.service.services import TemplateService


class TestTemplateService:
    """Test cases for TemplateService."""

    @pytest.fixture
    def template_service(self, mock_logger):
        """Create a TemplateService instance for testing."""
        return TemplateService(logger=mock_logger)

    def test_health_check_success(self, template_service, grpc_context):
        """Test successful health check."""
        request = HealthCheckRequest()
        response = template_service.HealthCheck(request, grpc_context)

        assert isinstance(response, HealthCheckResponse)
        assert response.status == HealthCheckResponse.Status.SERVING
        assert response.message == "Service is healthy"

    def test_health_check_exception_handling(self, template_service, grpc_context):
        """Test health check exception handling."""
        request = HealthCheckRequest()

        # Mock an internal method to raise an exception
        with patch.object(
            template_service._logger, "debug", side_effect=Exception("Test error")
        ):
            response = template_service.HealthCheck(request, grpc_context)

        assert isinstance(response, HealthCheckResponse)
        assert response.status == HealthCheckResponse.Status.NOT_SERVING
        assert "Service is unhealthy" in response.message
