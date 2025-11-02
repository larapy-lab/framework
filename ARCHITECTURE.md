# Larapy Framework Architecture

## Core Concept

**Larapy is a standalone Python web framework** inspired by Laravel's elegant design patterns. It does NOT depend on FastAPI, Starlette, or any other existing web framework. Instead, it provides its own complete implementation of all necessary components.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Your Code: Controllers, Models, Routes, Views)            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  Larapy Framework Core                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ HTTP Layer (Custom Implementation)                   │  │
│  │  - Request/Response classes                          │  │
│  │  - Router (not FastAPI/Starlette)                    │  │
│  │  - Middleware pipeline                               │  │
│  │  - Controller dispatcher                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Database Layer (SQLAlchemy-based)                    │  │
│  │  - Query Builder                                     │  │
│  │  - Schema Builder                                    │  │
│  │  - Migrations                                        │  │
│  │  - Connection Manager                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Security Layer                                        │  │
│  │  - Authentication (bcrypt/argon2)                    │  │
│  │  - Authorization (Gates/Policies)                    │  │
│  │  - Encryption (cryptography)                         │  │
│  │  - Validation (77 rules)                             │  │
│  │  - CSRF Protection                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Service Container & IoC                              │  │
│  │  - Dependency Injection                              │  │
│  │  - Service Providers                                 │  │
│  │  - Facades                                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Console/Artisan (Custom CLI)                         │  │
│  │  - Command system (not click-based)                  │  │
│  │  - Task scheduling (croniter)                        │  │
│  │  - Kernel                                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Configuration System (Custom)                        │  │
│  │  - .env parser (not python-dotenv)                   │  │
│  │  - Python-based config files (not YAML)              │  │
│  │  - Repository pattern                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Additional Features                                   │  │
│  │  - Queue System                                      │  │
│  │  - Events & Broadcasting                             │  │
│  │  - Mail & Notifications                              │  │
│  │  - Cache System                                      │  │
│  │  - Logging                                           │  │
│  │  - Collections                                       │  │
│  │  - Filesystem/Storage                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│              Third-Party Dependencies                        │
│  - sqlalchemy (ORM)                                          │
│  - bcrypt/argon2 (Password hashing)                          │
│  - cryptography (Encryption)                                 │
│  - requests (HTTP client)                                    │
│  - pytz (Timezone)                                           │
│  - croniter (Cron expressions)                               │
│  + Optional: boto3, pusher, redis, celery, faker, etc.      │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. HTTP Layer (Custom Implementation)

Larapy implements its own HTTP layer without relying on FastAPI or Starlette:

- **Request Class**: `larapy/http/request.py`
  - Handles input data, headers, cookies, files
  - Provides Laravel-like methods: `input()`, `all()`, `only()`, `except()`
  - Route parameter binding

- **Response Class**: `larapy/http/response.py`
  - JSON responses, views, redirects
  - Status code management
  - Header manipulation

- **Router**: `larapy/routing/router.py`
  - Route registration (GET, POST, PUT, PATCH, DELETE)
  - Route groups, prefixes, middleware
  - Resource routing
  - Route model binding

- **Middleware Pipeline**: `larapy/pipeline/`
  - Before/after middleware execution
  - Global, route, and group middleware
  - Built-in middleware (CSRF, throttling, authentication)

### 2. Database Layer (SQLAlchemy-based)

- **Query Builder**: `larapy/database/query/builder.py`
  - Fluent interface for SQL queries
  - All WHERE clause variants
  - Joins, aggregates, subqueries

- **Schema Builder**: `larapy/database/schema/`
  - Database migrations
  - Table creation/modification
  - Index management

- **Connection Manager**: `larapy/database/connection.py`
  - Multiple database connections
  - Connection pooling
  - Transaction management

### 3. Console System (Custom CLI)

Larapy has its own console implementation:

- **Command**: `larapy/console/command.py`
  - Base command class
  - Argument/option parsing
  - Output formatting

- **Kernel**: `larapy/console/kernel.py`
  - Command registration
  - Command dispatching
  - Scheduling

- **Scheduler**: `larapy/console/scheduling/`
  - Cron-based task scheduling (using croniter)
  - Task frequency helpers
  - Environment-based execution

### 4. Configuration System (Custom)

No external dependencies for configuration:

- **Environment Loader**: `larapy/config/environment.py`
  - Custom .env file parser
  - Type casting (bool, int, float, list)
  - Default value handling

- **Repository**: `larapy/config/repository.py`
  - Dot notation access
  - Get/set configuration values
  - Configuration caching

- **Config Files**: Python-based (not YAML)
  - Located in `config/` directory
  - Return Python dictionaries
  - Support dynamic values

### 5. Security Layer

- **Authentication**: `larapy/auth/`
  - Guards and providers
  - Password hashing (bcrypt/argon2)
  - Token-based authentication
  - Session management

- **Authorization**: `larapy/auth/gate.py`
  - Gates for simple checks
  - Policies for model authorization
  - Ability checks

- **Validation**: `larapy/validation/`
  - 77 validation rules
  - Custom rule creation
  - Form request validation

- **Encryption**: `larapy/encryption/`
  - AES-256-CBC/GCM encryption
  - Secure key generation
  - MAC verification

## Dependencies

### Core Dependencies (Always Required)

```toml
dependencies = [
    # Database ORM
    "sqlalchemy>=2.0.0",
    
    # Security & Encryption
    "bcrypt>=4.0.0",           # Password hashing
    "argon2-cffi>=23.1.0",     # Alternative password hasher
    "cryptography>=41.0.0",    # Encryption/decryption
    
    # HTTP & Utilities
    "requests>=2.31.0",        # HTTP client for external requests
    "pytz>=2023.3",            # Timezone handling
    "croniter>=2.0.0",         # Cron expression parsing
]
```

**Total: 7 packages** (minimal core footprint)

### Optional Dependencies (Feature-specific)

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "faker>=20.0.0",  # Database seeding
]
database = [
    "asyncpg>=0.29.0",     # PostgreSQL async
    "aiomysql>=0.2.0",     # MySQL async
    "aiosqlite>=0.19.0",   # SQLite async
]
storage = [
    "boto3>=1.28.0",       # AWS S3
    "aiofiles>=23.2.0",    # Async file operations
]
queue = [
    "redis>=5.0.0",        # Redis queue driver
    "celery>=5.3.4",       # Celery backend
    "psutil>=5.9.0",       # Worker monitoring
]
broadcasting = [
    "pusher>=3.3.0",       # Pusher integration
    "redis>=5.0.0",        # Redis broadcasting
]
```

### NOT Used (Common Misconceptions)

❌ **FastAPI** - Framework has its own HTTP layer  
❌ **Starlette** - Framework has its own routing  
❌ **click** - Framework has its own console system  
❌ **python-dotenv** - Framework has custom .env parser  
❌ **pyyaml** - Config files are Python dictionaries  
❌ **Uvicorn** - Applications may use it, but framework doesn't require it

## Design Philosophy

### 1. Laravel-Inspired API

Larapy provides a Pythonic version of Laravel's elegant API:

```python
# Routing
router.get('/users', 'UserController@index')
router.post('/users', 'UserController@store')

# Eloquent-style queries (coming in future versions)
users = User.where('active', True).orderBy('name').get()

# Validation
validator = Validator.make(data, {
    'email': 'required|email',
    'password': 'required|min:8',
})
```

### 2. Service Container & IoC

Dependency injection throughout the framework:

```python
# Service provider registration
class AppServiceProvider(ServiceProvider):
    def register(self):
        self.app.bind('config', lambda app: Repository())
    
    def boot(self):
        # Bootstrap application services
        pass
```

### 3. Facades for Clean Access

Static-like interface to framework services:

```python
from larapy.support.facades import DB, Cache, Mail

DB.table('users').where('active', True).get()
Cache.remember('users', 3600, lambda: fetch_users())
Mail.to('user@example.com').send(WelcomeMail())
```

### 4. Middleware Pipeline

Request processing through middleware layers:

```python
class EnsureTokenIsValid(Middleware):
    def handle(self, request, next_handler):
        if not self.validate_token(request):
            return Response('Unauthorized', 401)
        return next_handler(request)
```

## Testing

Framework includes comprehensive test suite:

- **2,716 tests** passing
- **79% coverage** across all modules
- Integration tests for complex scenarios
- Unit tests for individual components

## Comparison with Other Frameworks

### vs FastAPI
- **FastAPI**: ASGI-first, async-native, OpenAPI integration
- **Larapy**: Laravel-inspired, full-stack MVC, ORM-focused

### vs Django
- **Django**: Batteries-included, monolithic, Django ORM
- **Larapy**: Laravel-inspired, modular, SQLAlchemy-based

### vs Flask
- **Flask**: Minimal, micro-framework, Werkzeug-based
- **Larapy**: Full-featured, Laravel patterns, comprehensive tools

### vs Laravel (PHP)
- **Laravel**: PHP-based, mature ecosystem, Eloquent ORM
- **Larapy**: Python port, 88-92% feature parity, SQLAlchemy ORM

## Future Roadmap

1. **ASGI Support**: Add optional ASGI compatibility layer
2. **Async ORM**: Async query builder and model operations
3. **Admin Panel**: Auto-generated admin interface
4. **API Resources**: Enhanced JSON transformation
5. **Real-time**: WebSocket support improvements
6. **Testing**: Laravel Dusk-like browser testing

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.
