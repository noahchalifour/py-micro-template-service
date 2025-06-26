"""
Main application entry point.

This module provides the main application setup, gRPC server configuration,
and graceful shutdown handling.
"""

import asyncio
import signal
import sys
import logging
import functools
from concurrent import futures
from typing import Optional

from grpc_reflection.v1alpha import reflection
import grpc
from py_micro.service.config.logging_config import LoggingConfig
import structlog
from dependency_injector.wiring import inject, Provide, as_

from py_micro.model import template_service_pb2
from py_micro.model.template_service_pb2_grpc import (
    add_TemplateServiceServicer_to_server,
)
from py_micro.service.containers import ApplicationContainer
from py_micro.service.config import ApplicationConfig, ServerConfig
from py_micro.service.services import TemplateService


class GrpcServer:
    """
    gRPC server wrapper with lifecycle management.

    This class handles server startup, shutdown, and graceful termination.
    """

    @inject
    def __init__(
        self,
        config: dict = Provide["config.server"],
        template_service: TemplateService = Provide["services.template_service"],
        logger: structlog.BoundLogger = Provide["logger"],
    ) -> None:
        """
        Initialize the gRPC server.

        Args:
            config: Application configuration
            template_service: Template service instance
            logger: Structured logger
        """
        self._config = ServerConfig(**config)
        self._template_service = template_service
        self._logger = logger.bind(component="GrpcServer")
        self._server: Optional[grpc.aio.Server] = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """
        Start the gRPC server.

        This method sets up the server, registers services, and starts listening
        for incoming requests.
        """
        self._logger.info("Starting gRPC server")

        # Create server with thread pool
        self._server = grpc.aio.server(
            futures.ThreadPoolExecutor(max_workers=self._config.max_workers)
        )

        if self._server is None:
            self._logger.error("Failed to create server")
            return

        # Add services to server
        add_TemplateServiceServicer_to_server(self._template_service, self._server)

        # Enable reflection
        reflection.enable_server_reflection(
            (
                template_service_pb2.DESCRIPTOR.services_by_name[
                    "TemplateService"
                ].full_name,
                reflection.SERVICE_NAME,
            ),
            self._server,
        )

        # Configure server address
        listen_addr = f"{self._config.host}:{self._config.port}"
        self._server.add_insecure_port(listen_addr)

        # Start server
        await self._server.start()

        self._logger.info(
            "gRPC server started",
            host=self._config.host,
            port=self._config.port,
            max_workers=self._config.max_workers,
        )

        # Wait for shutdown signal
        await self._shutdown_event.wait()

    async def stop(self) -> None:
        """
        Stop the gRPC server gracefully.

        This method handles graceful shutdown with a configurable grace period.
        """
        if not self._server:
            return

        self._logger.info("Stopping gRPC server")

        # Signal shutdown
        self._shutdown_event.set()

        # Graceful shutdown
        await self._server.stop(self._config.grace_period)

        self._logger.info("gRPC server stopped")

    def handle_signal(self, signum: int) -> None:
        """
        Handle shutdown signals.

        Args:
            signum: Signal number
        """
        self._logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(self.stop())


def setup_logging(config: LoggingConfig) -> None:
    """
    Set up structured logging configuration.

    Args:
        config: Application configuration
    """
    logging.basicConfig(
        level=config.level,
    )

    if config.format == "json":
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


async def main() -> None:
    """
    Main application entry point.

    This function sets up dependency injection, configures logging,
    and starts the gRPC server.
    """
    # Initialize dependency injection container
    container = ApplicationContainer()
    container.wire(modules=[__name__])

    # Get configuration and set up logging
    config = container.config
    setup_logging(LoggingConfig(**config.logging()))

    # Get logger
    logger = container.logger()
    logger.info(
        "Starting application",
        app_name=config.app_name(),
        version=config.version(),
        environment=config.environment(),
    )

    # Create and configure server
    grpc_server = GrpcServer()

    # Register signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(
        signal.SIGINT,
        functools.partial(grpc_server.handle_signal, signal.SIGINT),
    )
    loop.add_signal_handler(
        signal.SIGTERM,
        functools.partial(grpc_server.handle_signal, signal.SIGTERM),
    )

    try:
        # Start server
        await grpc_server.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Application error", error=str(e))
        logger.exception(e)
        sys.exit(1)
    finally:
        # Cleanup
        await grpc_server.stop()
        logger.info("Application shutdown complete")


def run() -> None:
    """
    Synchronous entry point for the application.

    This function is used as the console script entry point.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    run()
