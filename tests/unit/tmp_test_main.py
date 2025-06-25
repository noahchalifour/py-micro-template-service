"""
Tests for the main application module.

This module tests the gRPC server lifecycle, signal handling,
and application startup/shutdown functionality.
"""

import asyncio
import signal
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest
import grpc

from py_micro.service.main import GrpcServer, main, run
from py_micro.service.config import Config
from py_micro.service.services.user_service import UserService


class TestSetupLogging:
    """Test cases for setup_logging function."""

    @patch("structlog.configure")
    def test_setup_logging_json_format(self, mock_configure):
        """Test logging setup with JSON format."""
        config = Config()
        config.logging.format = "json"

        setup_logging(config)

        mock_configure.assert_called_once()
        call_args = mock_configure.call_args[1]

        # Check that JSON renderer is in processors
        processors = call_args["processors"]
        processor_names = [proc.__class__.__name__ for proc in processors]
        assert "JSONRenderer" in processor_names

    @patch("structlog.configure")
    def test_setup_logging_console_format(self, mock_configure):
        """Test logging setup with console format."""
        config = Config()
        config.logging.format = "console"

        setup_logging(config)

        mock_configure.assert_called_once()
        call_args = mock_configure.call_args[1]

        # Check that console renderer is in processors
        processors = call_args["processors"]
        processor_names = [proc.__class__.__name__ for proc in processors]
        assert "ConsoleRenderer" in processor_names

    @patch("structlog.configure")
    def test_setup_logging_default_processors(self, mock_configure):
        """Test that default processors are included in logging setup."""
        config = Config()

        setup_logging(config)

        mock_configure.assert_called_once()
        call_args = mock_configure.call_args[1]

        # Check common processors
        processors = call_args["processors"]
        processor_names = [
            proc.__name__ if hasattr(proc, "__name__") else proc.__class__.__name__
            for proc in processors
        ]

        expected_processors = [
            "filter_by_level",
            "add_logger_name",
            "add_log_level",
            "TimeStamper",
        ]

        for expected in expected_processors:
            assert any(expected in name for name in processor_names), (
                f"Missing processor: {expected}"
            )

    @patch("structlog.configure")
    def test_setup_logging_configuration_options(self, mock_configure):
        """Test that logging configuration includes expected options."""
        config = Config()

        setup_logging(config)

        mock_configure.assert_called_once()
        call_args = mock_configure.call_args[1]

        # Check configuration options
        assert call_args["context_class"] == dict
        assert call_args["cache_logger_on_first_use"] is True
        assert call_args["logger_factory"].__class__.__name__ == "LoggerFactory"
        assert call_args["wrapper_class"].__name__ == "BoundLogger"


class TestGrpcServer:
    """Test cases for GrpcServer."""

    @pytest.fixture
    def mock_dependencies(self, mock_logger, test_config):
        """Create mock dependencies for GrpcServer."""
        mock_user_service = Mock(spec=UserService)
        return {
            "config": test_config,
            "user_service": mock_user_service,
            "logger": mock_logger,
        }

    def test_initialization(self, mock_dependencies):
        """Test GrpcServer initialization."""
        server = GrpcServer(**mock_dependencies)

        assert server._config == mock_dependencies["config"]
        assert server._user_service == mock_dependencies["user_service"]
        assert server._logger == mock_dependencies["logger"]
        assert server._server is None
        assert isinstance(server._shutdown_event, asyncio.Event)

        # Verify logger was bound
        mock_dependencies["logger"].bind.assert_called_once_with(component="GrpcServer")

    @patch("grpc.server")
    @patch("generated.user_service_pb2_grpc.add_UserServiceServicer_to_server")
    async def test_start_success(
        self, mock_add_servicer, mock_grpc_server, mock_dependencies
    ):
        """Test successful server start."""
        # Setup mocks
        mock_server = Mock()
        mock_server.start = AsyncMock()
        mock_grpc_server.return_value = mock_server

        server = GrpcServer(**mock_dependencies)

        # Create a task that will complete the shutdown event quickly
        async def complete_shutdown():
            await asyncio.sleep(0.01)
            server._shutdown_event.set()

        # Start both tasks
        start_task = asyncio.create_task(server.start())
        shutdown_task = asyncio.create_task(complete_shutdown())

        # Wait for both to complete
        await asyncio.gather(start_task, shutdown_task)

        # Verify server setup
        mock_grpc_server.assert_called_once()
        mock_add_servicer.assert_called_once_with(
            mock_dependencies["user_service"], mock_server
        )
        mock_server.add_insecure_port.assert_called_once_with("0.0.0.0:50051")
        mock_server.start.assert_called_once()

    @patch("grpc.server")
    async def test_start_with_custom_config(self, mock_grpc_server, mock_dependencies):
        """Test server start with custom configuration."""
        # Modify config
        mock_dependencies["config"].server.host = "127.0.0.1"
        mock_dependencies["config"].server.port = 8080
        mock_dependencies["config"].server.max_workers = 20

        mock_server = Mock()
        mock_server.start = AsyncMock()
        mock_grpc_server.return_value = mock_server

        server = GrpcServer(**mock_dependencies)

        # Complete shutdown event quickly
        async def complete_shutdown():
            await asyncio.sleep(0.01)
            server._shutdown_event.set()

        start_task = asyncio.create_task(server.start())
        shutdown_task = asyncio.create_task(complete_shutdown())

        await asyncio.gather(start_task, shutdown_task)

        # Verify custom configuration was used
        mock_server.add_insecure_port.assert_called_once_with("127.0.0.1:8080")

    async def test_stop_without_server(self, mock_dependencies):
        """Test stop method when no server is running."""
        server = GrpcServer(**mock_dependencies)

        # Should not raise an exception
        await server.stop()

        assert server._shutdown_event.is_set()

    async def test_stop_with_server(self, mock_dependencies):
        """Test stop method with running server."""
        server = GrpcServer(**mock_dependencies)

        # Mock server
        mock_server = Mock()
        mock_server.stop = AsyncMock()
        server._server = mock_server

        await server.stop()

        assert server._shutdown_event.is_set()
        mock_server.stop.assert_called_once_with(
            mock_dependencies["config"].server.grace_period
        )

    def test_handle_signal(self, mock_dependencies):
        """Test signal handling."""
        server = GrpcServer(**mock_dependencies)

        with patch("asyncio.create_task") as mock_create_task:
            server.handle_signal(signal.SIGINT, None)

            mock_create_task.assert_called_once()
            # Verify that stop() coroutine was passed to create_task
            args = mock_create_task.call_args[0]
            assert asyncio.iscoroutine(args[0])


class TestMainFunction:
    """Test cases for main application function."""

    @patch("py_micro.service.main.Container")
    @patch("py_micro.service.main.setup_logging")
    @patch("py_micro.service.main.GrpcServer")
    @patch("signal.signal")
    async def test_main_success(
        self,
        mock_signal,
        mock_grpc_server_class,
        mock_setup_logging,
        mock_container_class,
    ):
        """Test successful main function execution."""
        # Setup mocks
        mock_container = Mock()
        mock_config = Mock()
        mock_config.app_name = "test-app"
        mock_config.version = "1.0.0"
        mock_config.environment = "test"
        mock_logger = Mock()
        mock_user_service = Mock()

        mock_container.config.return_value = mock_config
        mock_container.logger.return_value = mock_logger
        mock_container.user_service.return_value = mock_user_service
        mock_container.wire = Mock()

        mock_container_class.return_value = mock_container

        mock_grpc_server = Mock()
        mock_grpc_server.start = AsyncMock()
        mock_grpc_server.stop = AsyncMock()
        mock_grpc_server_class.return_value = mock_grpc_server

        # Mock to complete quickly
        async def quick_start():
            await asyncio.sleep(0.01)
            raise KeyboardInterrupt()

        mock_grpc_server.start.side_effect = quick_start

        # Run main function
        await main()

        # Verify setup
        mock_container_class.assert_called_once()
        mock_container.wire.assert_called_once()
        mock_setup_logging.assert_called_once_with(mock_config)
        mock_grpc_server_class.assert_called_once()
        mock_grpc_server.start.assert_called_once()
        mock_grpc_server.stop.assert_called_once()

        # Verify signal handlers were set up
        assert mock_signal.call_count == 2
        signal_calls = [call[0] for call in mock_signal.call_args_list]
        assert (signal.SIGINT, mock_signal.call_args_list[0][0][1]) in signal_calls
        assert (signal.SIGTERM, mock_signal.call_args_list[1][0][1]) in signal_calls

    @patch("py_micro.service.main.Container")
    @patch("py_micro.service.main.setup_logging")
    @patch("py_micro.service.main.GrpcServer")
    @patch("signal.signal")
    async def test_main_exception_handling(
        self,
        mock_signal,
        mock_grpc_server_class,
        mock_setup_logging,
        mock_container_class,
    ):
        """Test main function exception handling."""
        # Setup mocks to raise exception
        mock_container_class.side_effect = Exception("Test error")

        with patch("sys.exit") as mock_exit:
            await main()
            mock_exit.assert_called_once_with(1)

    @patch("py_micro.service.main.Container")
    @patch("py_micro.service.main.setup_logging")
    @patch("py_micro.service.main.GrpcServer")
    @patch("signal.signal")
    async def test_main_keyboard_interrupt(
        self,
        mock_signal,
        mock_grpc_server_class,
        mock_setup_logging,
        mock_container_class,
    ):
        """Test main function keyboard interrupt handling."""
        # Setup mocks
        mock_container = Mock()
        mock_config = Mock()
        mock_config.app_name = "test-app"
        mock_config.version = "1.0.0"
        mock_config.environment = "test"
        mock_logger = Mock()

        mock_container.config.return_value = mock_config
        mock_container.logger.return_value = mock_logger
        mock_container.wire = Mock()
        mock_container_class.return_value = mock_container

        mock_grpc_server = Mock()
        mock_grpc_server.start = AsyncMock(side_effect=KeyboardInterrupt())
        mock_grpc_server.stop = AsyncMock()
        mock_grpc_server_class.return_value = mock_grpc_server

        # Should not raise an exception
        await main()

        # Verify cleanup was called
        mock_grpc_server.stop.assert_called_once()


class TestRunFunction:
    """Test cases for run function."""

    @patch("py_micro.service.main.asyncio.run")
    def test_run_success(self, mock_asyncio_run):
        """Test successful run function execution."""
        mock_asyncio_run.return_value = None

        run()

        mock_asyncio_run.assert_called_once()
        # Verify that main() coroutine was passed
        args = mock_asyncio_run.call_args[0]
        assert asyncio.iscoroutine(args[0])

    @patch("py_micro.service.main.asyncio.run")
    @patch("sys.exit")
    def test_run_keyboard_interrupt(self, mock_exit, mock_asyncio_run):
        """Test run function keyboard interrupt handling."""
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        run()

        mock_exit.assert_called_once_with(0)

    @patch("py_micro.service.main.asyncio.run")
    @patch("sys.exit")
    @patch("builtins.print")
    def test_run_exception_handling(self, mock_print, mock_exit, mock_asyncio_run):
        """Test run function exception handling."""
        mock_asyncio_run.side_effect = Exception("Test error")

        run()

        mock_print.assert_called_once_with("Application failed to start: Test error")
        mock_exit.assert_called_once_with(1)

    @patch("py_micro.service.main.asyncio.run")
    @patch("builtins.print")
    def test_run_keyboard_interrupt_message(self, mock_print, mock_asyncio_run):
        """Test run function keyboard interrupt message."""
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        with patch("sys.exit"):
            run()

        mock_print.assert_called_once_with("Application interrupted by user")
