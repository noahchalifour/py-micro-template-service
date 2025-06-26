"""
Template service implementation.
"""

from modelrepo.repository import ModelRepository
from datetime import datetime
import grpc
import structlog
from dependency_injector.wiring import inject, Provide

from py_micro.model.template_service_pb2 import (
    HealthCheckRequest,
    HealthCheckResponse,
)
from py_micro.model.template_service_pb2_grpc import TemplateServiceServicer
from py_micro.service.validators.common import validate_less_than


class TemplateService(TemplateServiceServicer):
    """
    gRPC Template Service implementation.
    """

    @inject
    def __init__(
        self,
        logger: structlog.BoundLogger = Provide["logger"],
        health_check_repository: ModelRepository = Provide["repositories.health_check"],
    ) -> None:
        """
        Initialize the template service.

        Args:
            logger: Structured logger instance
        """
        self._logger = logger.bind(service="TemplateService")
        self._health_check_repository = health_check_repository

        self._logger.info("TemplateService initialized")

    def HealthCheck(
        self,
        request: HealthCheckRequest,
        context: grpc.ServicerContext,
    ) -> HealthCheckResponse:
        """
        Health check endpoint.

        As a test, this will only work 3 times, on the 4rd time it should
        return an invalid request (this is to test the validators)

        Args:
            request: Health check request (empty)
            context: gRPC service context

        Returns:
            Health check response with service status
        """
        existing_checks = self._health_check_repository.count({})

        validate_less_than(
            existing_checks,
            less_than=3,
            code=grpc.StatusCode.RESOURCE_EXHAUSTED,
            message="You've exceeded the maximum number of health checks.",
            context=context,
        )

        try:
            self._logger.debug("Health check requested")

            health_check = self._health_check_repository.create(
                {
                    "timestamp": datetime.now(),
                }
            )
            self._logger.debug("Created health check record", record=health_check)

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
