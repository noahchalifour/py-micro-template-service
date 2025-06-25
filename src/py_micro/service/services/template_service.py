"""
Template service implementation.
"""

import grpc
import structlog
from dependency_injector.wiring import inject, Provide

# Import generated gRPC code
from py_micro.model.template_service_pb2 import (
    HealthCheckRequest,
    HealthCheckResponse,
)
from py_micro.model.template_service_pb2_grpc import TemplateServiceServicer


class TemplateService(TemplateServiceServicer):
    """
    gRPC Template Service implementation.
    """

    @inject
    def __init__(
        self,
        logger: structlog.BoundLogger = Provide["logger"],
    ) -> None:
        """
        Initialize the template service.

        Args:
            logger: Structured logger instance
        """
        self._logger = logger.bind(service="TemplateService")

        self._logger.info("TemplateService initialized")

    def HealthCheck(
        self,
        request: HealthCheckRequest,
        context: grpc.ServicerContext,
    ) -> HealthCheckResponse:
        """
        Health check endpoint.

        Args:
            request: Health check request (empty)
            context: gRPC service context

        Returns:
            Health check response with service status
        """
        try:
            self._logger.debug("Health check requested")

            # In a real implementation, you would check:
            # - Database connectivity
            # - External service dependencies
            # - Resource availability

            return HealthCheckResponse(
                status=HealthCheckResponse.Status.SERVING,
                message="Service is healthy",
            )

        except Exception as e:
            self._logger.error("Health check failed", error=str(e))
            return HealthCheckResponse(
                status=HealthCheckResponse.Status.NOT_SERVING,
                message=f"Service is unhealthy: {str(e)}",
            )
