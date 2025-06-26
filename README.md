# py-micro-service

A production-ready Python microservice template built with gRPC, dependency injection, and best practices.

## Overview

This microservice template provides:
- **gRPC API** - High-performance, type-safe inter-service communication
- **Dependency Injection** - Clean architecture with dependency-injector
- **Structured Logging** - JSON and console logging with structlog
- **Configuration Management** - Environment-based config with Pydantic
- **Comprehensive Testing** - 100% test coverage with pytest
- **Type Safety** - Full type hints and mypy validation
- **Code Quality** - Black, isort, and flake8 for consistent code style

## Features

### Core Functionality
- User management CRUD operations (example implementation)
- Health check endpoint
- Graceful shutdown handling
- Signal handling (SIGINT, SIGTERM)

### Architecture
- Clean separation of concerns
- Repository pattern ready (with example implementation)
- Modular container-based dependency injection
- Environment-based configuration
- Structured error handling

### Development Experience
- Hot reloading in development
- Comprehensive test suite
- Code generation from proto definitions
- Docker support
- Make-based build system

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry
- Make (optional, for convenience commands)

### Installation

1. **Set up the model repository first:**
```bash
cd ../py-micro-model
make install
make generate
```

2. **Install service dependencies:**
```bash
make install
# or
poetry install
```

4. **Run tests:**
```bash
make test
```

5. **Start the service:**
```bash
make run
# or
poetry run microservice
```

## Directory Structure

```
py-micro-service/
├── src/py_micro/service/       # Main application code
│   ├── config/                 # Configuration management
│   ├── containers/             # Dependency injection containers
│   ├── services/               # gRPC service implementations
│   └── main.py                 # Application entry point
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── conftest.py             # Test configuration
├── Makefile                    # Build automation
├── pyproject.toml              # Poetry configuration
└── README.md                   # This file
```

## Configuration

The service uses environment-based configuration with sensible defaults:

### Server Configuration
```bash
SERVER_HOST=0.0.0.0          # Server host (default: 0.0.0.0)
SERVER_PORT=50051            # Server port (default: 50051)
SERVER_MAX_WORKERS=10        # Max worker threads (default: 10)
SERVER_GRACE_PERIOD=30       # Shutdown grace period (default: 30)
```

### Logging Configuration
```bash
LOGGING_LEVEL=INFO           # Log level (default: INFO)
LOGGING_FORMAT=json          # Log format: json|console (default: json)
```

### Application Configuration
```bash
APP_NAME=my-service          # Application name
VERSION=1.0.0               # Application version
DEBUG=false                 # Debug mode (default: false)
ENVIRONMENT=production      # Environment name (default: development)
```

## Usage

### Running the Service

**Development:**
```bash
make dev-run
# or
poetry run python -m py_micro.service.main
```

**Production:**
```bash
make run
# or
poetry run microservice
```

### Testing the Service

The service provides a gRPC API. You can test it using:

1. **grpcurl** (recommended):
```bash
# Health check
grpcurl -plaintext localhost:50051 user_service.v1.UserService/HealthCheck
```

2. **Python client** (see integration tests for examples)

3. **Postman** with gRPC support

## Development

### Adding New Services

1. **Define the service in the model repository:**
```protobuf
// In py-micro-model/proto/my_service.proto
service MyService {
    rpc MyMethod(MyRequest) returns (MyResponse);
}
```

2. **Implement the service:**
```python
# In src/py_micro/service/services/my_service.py
from generated.my_service_pb2_grpc import MyServiceServicer

class MyService(MyServiceServicer):
    def MyMethod(self, request, context):
        # Implementation here
        pass
```

3. **Register in container:**
```python
# In src/py_micro/service/containers/__init__.py
my_service = providers.Factory(MyService, ...)
```

4. **Add to server:**
```python
# In src/py_micro/service/main.py
from generated.my_service_pb2_grpc import add_MyServiceServicer_to_server
add_MyServiceServicer_to_server(my_service, self._server)
```

### Testing

**Run all tests:**
```bash
make test
```

**Run specific test types:**
```bash
make test-unit          # Unit tests only
make test-integration   # Integration tests only
```

**Generate coverage report:**
```bash
make coverage
# Open htmlcov/index.html to view detailed coverage
```

**Watch mode for development:**
```bash
make dev-test-watch
```

### Code Quality

**Format code:**
```bash
make format
```

**Run linting:**
```bash
make lint
```

**Type checking:**
```bash
poetry run mypy src/
```

### Building and Deployment

**Build package:**
```bash
make build
```

**Docker (if Dockerfile is added):**
```bash
make docker-build
make docker-run
```

## Contributing

1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation
4. Run the full test suite before submitting

## License

This template is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test cases for usage examples
3. Check the generated documentation

