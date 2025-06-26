"""
Integration tests for the py_micro.service.

This module provides end-to-end integration tests that verify
the complete functionality of the microservice including
dependency injection, gRPC communication, and service behavior.
"""

import grpc
import pytest
import pytest_asyncio
from concurrent import futures

from py_micro.model.template_service_pb2 import (
    HealthCheckRequest,
)
from py_micro.model.template_service_pb2_grpc import (
    TemplateServiceStub,
    add_TemplateServiceServicer_to_server,
)
from py_micro.service.containers import ApplicationContainer
from py_micro.service.template_service import TemplateService


class TestMicroserviceIntegration:
    """Integration tests for the complete py_micro.service."""

    @pytest_asyncio.fixture
    async def grpc_server_and_channel(self):
        """Set up a test gRPC server and client channel."""
        # Create container and wire dependencies
        container = ApplicationContainer()
        container.wire(modules=["py_micro.service.template_service"])

        # Create server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # Add service to server
        services = container.services
        template_service = services.template_service()
        add_TemplateServiceServicer_to_server(template_service, server)

        # Start server on a test port
        test_port = 50052
        listen_addr = f"localhost:{test_port}"
        server.add_insecure_port(listen_addr)

        server.start()

        # Create client channel
        channel = grpc.aio.insecure_channel(listen_addr)

        yield server, channel, container

        # Cleanup
        await channel.close()
        server.stop(grace=1)

    @pytest.mark.asyncio
    async def test_health_check(self, grpc_server_and_channel):
        """Test health check endpoint."""
        server, channel, container = grpc_server_and_channel
        stub = TemplateServiceStub(channel)

        health_request = HealthCheckRequest()
        health_response = await stub.HealthCheck(health_request)

        assert health_response.status == health_response.Status.SERVING
        assert health_response.message == "Service is healthy"

    @pytest.mark.asyncio
    async def test_dependency_injection_wiring(self, grpc_server_and_channel):
        """Test that dependency injection is properly wired."""
        server, channel, container = grpc_server_and_channel

        # Get the template service from the container
        template_service = container.services.template_service()

        # Verify it's properly configured
        assert isinstance(template_service, TemplateService)
        assert template_service._logger is not None
