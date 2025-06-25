"""
Integration tests for the py_micro.service.

This module provides end-to-end integration tests that verify
the complete functionality of the microservice including
dependency injection, gRPC communication, and service behavior.
"""

import asyncio
import grpc
import pytest
from concurrent import futures
from unittest.mock import patch

from generated.user_service_pb2 import (
    CreateUserRequest,
    GetUserRequest,
    ListUsersRequest,
    UpdateUserRequest,
    DeleteUserRequest,
    HealthCheckRequest,
)
from generated.user_service_pb2_grpc import UserServiceStub, add_UserServiceServicer_to_server
from py_micro.service.containers import Container
from py_micro.service.services.user_service import UserService


class TestMicroserviceIntegration:
    """Integration tests for the complete py_micro.service."""
    
    @pytest.fixture
    async def grpc_server_and_channel(self):
        """Set up a test gRPC server and client channel."""
        # Create container and wire dependencies
        container = Container()
        container.wire(modules=["py_micro.service.services.user_service"])
        
        # Create server
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # Add service to server
        user_service = container.user_service()
        add_UserServiceServicer_to_server(user_service, server)
        
        # Start server on a test port
        test_port = 50052
        listen_addr = f"localhost:{test_port}"
        server.add_insecure_port(listen_addr)
        
        await server.start()
        
        # Create client channel
        channel = grpc.aio.insecure_channel(listen_addr)
        
        yield server, channel, container
        
        # Cleanup
        await channel.close()
        await server.stop(grace=1)
    
    async def test_complete_user_lifecycle(self, grpc_server_and_channel):
        """Test complete user lifecycle: create, get, update, delete."""
        server, channel, container = grpc_server_and_channel
        stub = UserServiceStub(channel)
        
        # 1. Create a user
        create_request = CreateUserRequest(
            email="integration@test.com",
            first_name="Integration",
            last_name="Test",
        )
        
        create_response = await stub.CreateUser(create_request)
        assert create_response.user.email == "integration@test.com"
        assert create_response.user.first_name == "Integration"
        assert create_response.user.last_name == "Test"
        assert create_response.user.is_active is True
        
        user_id = create_response.user.id
        assert user_id  # Should have an ID
        
        # 2. Get the user
        get_request = GetUserRequest(id=user_id)
        get_response = await stub.GetUser(get_request)
        assert get_response.user.id == user_id
        assert get_response.user.email == "integration@test.com"
        
        # 3. Update the user
        update_request = UpdateUserRequest(
            id=user_id,
            email="updated@test.com",
            first_name="Updated",
            is_active=False,
        )
        
        update_response = await stub.UpdateUser(update_request)
        assert update_response.user.id == user_id
        assert update_response.user.email == "updated@test.com"
        assert update_response.user.first_name == "Updated"
        assert update_response.user.is_active is False
        
        # 4. Verify the update by getting the user again
        get_response_2 = await stub.GetUser(get_request)
        assert get_response_2.user.email == "updated@test.com"
        assert get_response_2.user.first_name == "Updated"
        assert get_response_2.user.is_active is False
        
        # 5. Delete the user
        delete_request = DeleteUserRequest(id=user_id)
        delete_response = await stub.DeleteUser(delete_request)
        assert delete_response.success is True
        
        # 6. Verify the user is deleted
        try:
            await stub.GetUser(get_request)
            assert False, "Expected user to be deleted"
        except grpc.RpcError as e:
            assert e.code() == grpc.StatusCode.NOT_FOUND
    
    async def test_list_users_with_pagination(self, grpc_server_and_channel):
        """Test user listing with pagination."""
        server, channel, container = grpc_server_and_channel
        stub = UserServiceStub(channel)
        
        # Create multiple users
        user_ids = []
        for i in range(5):
            create_request = CreateUserRequest(
                email=f"user{i}@test.com",
                first_name=f"User{i}",
                last_name="Test",
            )
            create_response = await stub.CreateUser(create_request)
            user_ids.append(create_response.user.id)
        
        # Test first page
        list_request = ListUsersRequest(page_size=2)
        list_response = await stub.ListUsers(list_request)
        
        assert len(list_response.users) == 2
        assert list_response.total_count == 5
        assert list_response.next_page_token == "2"
        
        # Test second page
        list_request_2 = ListUsersRequest(page_size=2, page_token="2")
        list_response_2 = await stub.ListUsers(list_request_2)
        
        assert len(list_response_2.users) == 2
        assert list_response_2.total_count == 5
        assert list_response_2.next_page_token == "4"
        
        # Test final page
        list_request_3 = ListUsersRequest(page_size=2, page_token="4")
        list_response_3 = await stub.ListUsers(list_request_3)
        
        assert len(list_response_3.users) == 1
        assert list_response_3.total_count == 5
        assert list_response_3.next_page_token == ""
    
    async def test_error_handling(self, grpc_server_and_channel):
        """Test error handling in gRPC calls."""
        server, channel, container = grpc_server_and_channel
        stub = UserServiceStub(channel)
        
        # Test creating user without email
        try:
            create_request = CreateUserRequest(
                first_name="No",
                last_name="Email",
            )
            await stub.CreateUser(create_request)
            assert False, "Expected validation error"
        except grpc.RpcError as e:
            assert e.code() == grpc.StatusCode.INVALID_ARGUMENT
            assert "Email is required" in e.details()
        
        # Test getting non-existent user
        try:
            get_request = GetUserRequest(id="non-existent-id")
            await stub.GetUser(get_request)
            assert False, "Expected not found error"
        except grpc.RpcError as e:
            assert e.code() == grpc.StatusCode.NOT_FOUND
            assert "User not found" in e.details()
        
        # Test duplicate email
        create_request = CreateUserRequest(
            email="duplicate@test.com",
            first_name="First",
            last_name="User",
        )
        await stub.CreateUser(create_request)
        
        try:
            create_request_2 = CreateUserRequest(
                email="duplicate@test.com",
                first_name="Second",
                last_name="User",
            )
            await stub.CreateUser(create_request_2)
            assert False, "Expected duplicate email error"
        except grpc.RpcError as e:
            assert e.code() == grpc.StatusCode.ALREADY_EXISTS
            assert "already exists" in e.details()
    
    async def test_health_check(self, grpc_server_and_channel):
        """Test health check endpoint."""
        server, channel, container = grpc_server_and_channel
        stub = UserServiceStub(channel)
        
        health_request = HealthCheckRequest()
        health_response = await stub.HealthCheck(health_request)
        
        assert health_response.status == health_response.Status.SERVING
        assert health_response.message == "Service is healthy"
    
    async def test_dependency_injection_wiring(self, grpc_server_and_channel):
        """Test that dependency injection is properly wired."""
        server, channel, container = grpc_server_and_channel
        
        # Get the user service from the container
        user_service = container.user_service()
        
        # Verify it's properly configured
        assert isinstance(user_service, UserService)
        assert user_service._config is not None
        assert user_service._logger is not None
        
        # Verify the service has the expected empty state
        assert len(user_service._users) == 0
    
    async def test_concurrent_operations(self, grpc_server_and_channel):
        """Test concurrent operations on the service."""
        server, channel, container = grpc_server_and_channel
        stub = UserServiceStub(channel)
        
        # Create multiple users concurrently
        async def create_user(index):
            create_request = CreateUserRequest(
                email=f"concurrent{index}@test.com",
                first_name=f"User{index}",
                last_name="Concurrent",
            )
            return await stub.CreateUser(create_request)
        
        # Run 5 concurrent user creations
        tasks = [create_user(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # Verify all users were created successfully
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert response.user.email == f"concurrent{i}@test.com"
            assert response.user.first_name == f"User{i}"
        
        # Verify they can all be retrieved
        list_request = ListUsersRequest(page_size=10)
        list_response = await stub.ListUsers(list_request)
        assert len(list_response.users) == 5
        assert list_response.total_count == 5

