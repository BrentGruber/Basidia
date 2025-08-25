# Basidia Project Plan

## Project Overview
Basidia is an async Python microservices framework inspired by Nameko, designed to support multiple message brokers with modern async/await patterns and comprehensive type hinting.

## MVP Definition

### Core Features (MVP)
1. **RPC Service Decorators** - `@rpc` decorator for exposing async methods
2. **Basic AMQP/RabbitMQ Support** - Producer/Consumer with connection management
3. **Service Discovery** - Automatic service registration and discovery
4. **CLI Runner** - `basidia run` command to start services
5. **Basic Dependency Injection** - Service dependencies and configuration
6. **Type Safety** - Full type hinting and validation

### MVP Success Criteria
- Services can be defined with simple decorators
- RPC calls work reliably over AMQP
- Services can be started with CLI commands
- Basic error handling and logging
- Clear documentation and examples

## Sample User Code

### Basic Service Definition
```python
# services/greeting.py
from basidia import Service, rpc

class GreetingService(Service):
    name = "greeting_service"

    @rpc
    async def hello(self, name: str) -> str:
        return f"Hello, {name}!"

    @rpc
    async def goodbye(self, name: str) -> str:
        return f"Goodbye, {name}!"
```

### Service with Dependencies
```python
# services/user.py
from basidia import Service, rpc, Dependency

class DatabaseService(Service):
    name = "database_service"
    
    @rpc
    async def get_user(self, user_id: int) -> dict:
        # Mock database call
        return {"id": user_id, "name": f"User {user_id}"}

class UserService(Service):
    name = "user_service"
    
    db = Dependency("database_service")

    @rpc
    async def get_user_greeting(self, user_id: int) -> str:
        user = await self.db.get_user(user_id)
        return f"Hello, {user['name']}!"
```

### Event-Driven Service
```python
# services/notifications.py
from basidia import Service, event_handler, rpc

class NotificationService(Service):
    name = "notification_service"

    @event_handler("user.created")
    async def on_user_created(self, user_data: dict):
        print(f"Sending welcome email to {user_data['email']}")

    @rpc
    async def send_notification(self, message: str, recipient: str) -> bool:
        print(f"Notification sent to {recipient}: {message}")
        return True
```

### HTTP Service (via Starlette)
```python
# services/api.py
from basidia import Service, http_endpoint, Dependency
from starlette.responses import JSONResponse

class ApiService(Service):
    name = "api_service"
    
    user_service = Dependency("user_service")

    @http_endpoint("GET", "/users/{user_id}")
    async def get_user(self, request):
        user_id = int(request.path_params["user_id"])
        user = await self.user_service.get_user_greeting(user_id)
        return JSONResponse({"message": user})

    @http_endpoint("POST", "/users")
    async def create_user(self, request):
        data = await request.json()
        # Process user creation
        return JSONResponse({"status": "created", "user": data})
```

### Configuration and Environment
```python
# config.py
from basidia import Config

config = Config({
    "AMQP_URI": "amqp://user:password@localhost:5672/",
    "LOG_LEVEL": "INFO",
    "SERVICE_TIMEOUT": 30
})
```

### Running Services
```bash
# Start all services in a directory
basidia run services/

# Start specific service
basidia run services.greeting:GreetingService

# Interactive shell
basidia shell
>>> await rpc.greeting_service.hello("World")
'Hello, World!'
```

## Architectural Decisions & Options

### 1. Service Definition Pattern
**Decision**: Class-based services with decorators (similar to Nameko)
- **Pros**: Familiar pattern, easy dependency injection, clear service boundaries
- **Cons**: More verbose than function-based approaches
- **Alternative**: Function-based services with decorators

### 2. Message Broker Abstraction
**Decision**: Plugin-based broker system
```python
# Broker interface
class MessageBroker(ABC):
    async def connect(self) -> None: ...
    async def publish(self, routing_key: str, message: bytes) -> None: ...
    async def consume(self, queue: str, handler: Callable) -> None: ...
```
- **Priority Order**: AMQP (RabbitMQ), NATS, Apache Kafka, Redis Streams
- **MVP**: Start with AMQP only, design for pluggability
- **Next**: NATS implementation after AMQP is stable

### 3. Serialization Strategy
**Decision**: Pluggable serialization (default: msgpack)
- **Options**: msgpack (fast, compact), JSON (readable), Protocol Buffers
- **Consideration**: Type preservation and schema evolution

### 4. Dependency Injection
**Decision**: Declaration-based DI with runtime resolution
```python
class ServiceA(Service):
    service_b = Dependency("service_b")  # By name
    config = ConfigDependency("database.url")  # Configuration
    http_client = Dependency(HttpClient)  # By type
```

### 5. Error Handling & Reliability
**Options to Consider**:
- Circuit breaker pattern for service calls
- Automatic retry with exponential backoff
- Dead letter queues for failed messages
- Health checks and service monitoring

### 6. Testing Strategy
**Decision**: Built-in testing utilities
```python
from basidia.testing import ServiceTestCase

class TestGreetingService(ServiceTestCase):
    services = [GreetingService]
    
    async def test_hello(self):
        result = await self.rpc.greeting_service.hello("Test")
        assert result == "Hello, Test!"
```

### 7. CLI Design
**Commands to Implement**:
- `basidia run <service_path>` - Run services
- `basidia shell` - Interactive shell
- `basidia test` - Run tests
- `basidia worker` - Run as background worker

## Project Structure

```
basidia/
├── __init__.py          # Main API exports
├── service.py           # Service base class
├── decorators.py        # @rpc, @event_handler decorators
├── registry.py          # Service discovery/registration
├── config.py           # Configuration system
├── brokers/            # Message broker implementations
│   ├── __init__.py     # Broker interface
│   ├── base.py         # Abstract base broker
│   ├── memory.py       # In-memory broker
│   └── amqp.py         # AMQP/RabbitMQ broker
├── serializers/        # Message serialization
│   ├── __init__.py
│   ├── base.py
│   └── msgpack.py
├── cli/                # CLI commands
│   ├── __init__.py
│   ├── main.py
│   └── commands.py
├── testing/            # Testing utilities
│   ├── __init__.py
│   └── testcase.py
└── exceptions.py       # Custom exceptions
```

## Implementation Phases

### Phase 1: Core Foundation (MVP)
- [ ] Service base class and decorator system
- [ ] AMQP broker implementation
- [ ] Basic RPC functionality
- [ ] Service runner and CLI
- [ ] Configuration system
- [ ] Basic testing utilities

### Phase 2: Enhanced Features
- [ ] Event system (pub/sub)
- [ ] Advanced dependency injection
- [ ] Service discovery improvements
- [ ] Error handling and retries
- [ ] Logging and metrics

### Phase 3: HTTP & Additional Brokers
- [ ] HTTP endpoint support via Starlette
- [ ] Unified service interface for RPC and HTTP
- [ ] NATS broker implementation
- [ ] Advanced broker features

### Phase 4: Production Features
- [ ] Health checks and monitoring
- [ ] OpenTelemetry integration (metrics, tracing, logs)
- [ ] Service mesh integration
- [ ] Advanced testing utilities

## Technical Considerations

### Performance
- Connection pooling and reuse
- Async message processing with concurrency limits
- Efficient serialization (msgpack by default)
- Focus on simplicity over premature optimization
- Performance improvements can be added later based on real-world usage

### Reliability
- Automatic reconnection on connection loss
- Message acknowledgment and error handling
- Graceful shutdown handling
- Resource cleanup and memory management

### Developer Experience
- Rich type hinting throughout
- Clear error messages and debugging
- Comprehensive documentation
- IDE support and autocompletion

### Deployment & Configuration
- Docker container support
- Kubernetes deployment guides
- Process management (systemd, supervisor)
- Flexible configuration: environment variables and config files
- Configuration precedence: CLI args > env vars > config files > defaults

### Monitoring & Observability
- Built-in OpenTelemetry integration
- Automatic instrumentation for RPC calls and HTTP requests
- Custom metrics and tracing support
- Structured logging with correlation IDs

## Architectural Decisions Made

1. **Service Definition**: ✅ Class-based services with decorators
2. **Broker Priority**: ✅ NATS will be the second broker after AMQP
3. **HTTP Support**: ✅ Include HTTP endpoints via Starlette integration
4. **Compatibility**: ✅ Nameko compatibility not required - focus on inspiration over migration
5. **Performance vs Simplicity**: ✅ Prioritize simplicity, optimize later based on real usage
6. **Testing Strategy**: ✅ Support both in-process and external broker testing
7. **Configuration**: ✅ Support both environment variables and config files
8. **Monitoring**: ✅ Built-in OpenTelemetry integration for metrics, tracing, and logs

## Success Metrics
- Time to create first working service < 5 minutes
- RPC latency < 1ms overhead over broker
- Memory usage < 50MB for basic service
- 100% type coverage
- Comprehensive test coverage (>90%)
- Clear migration path from Nameko