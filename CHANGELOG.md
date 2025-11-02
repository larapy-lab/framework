# Changelog

All notable changes to the Larapy framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2025-11-02

### Added

- Multi-repository architecture (framework, installer, application template, documentation)
- Comprehensive test suite with 2,716 passing tests
- 79% test coverage across framework
- Eloquent ORM with full relationship support (BelongsTo, HasMany, HasOne, BelongsToMany, HasManyThrough, MorphTo, MorphMany, MorphToMany)
- Query caching with configurable TTL
- Eager loading with nested relationships
- Polymorphic relationships
- Authentication system with Guards and Sanctum-style token authentication
- Authorization with Gates and Policies
- Mail system with SMTP transport and multiple providers
- Queue system with Redis, Database, and Sync drivers
- Cache system with Redis, File, and Database stores
- Event system with listeners and subscribers
- Comprehensive validation with 50+ rules
- Database migrations and seeding
- Artisan console with 20+ commands
- HTTP middleware (CORS, rate limiting, authentication)
- JSON API resources with conditional attributes
- Collection class with 50+ methods
- Service container with dependency injection
- Configuration management with environment variables
- Logging with multiple channels
- Encryption and hashing services
- Filesystem abstraction with local and cloud storage
- Broadcasting system for real-time events

### Changed

- Repository structure from monorepo to multi-repo
- Package name from `larapy` to `larapy-framework`
- Installation method to use `larapy-installer`

### Security

- Bcrypt and Argon2 hashing with configurable rounds
- CSRF protection middleware
- SQL injection prevention via parameterized queries
- XSS protection in views
- Encryption service with key rotation support

## [0.1.0] - 2025-10-01

### Added

- Initial framework release
- Basic routing and middleware
- Eloquent ORM foundation
- Authentication system
- Database migrations
- Console commands

[Unreleased]: https://github.com/larapy-lab/framework/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/larapy-lab/framework/releases/tag/v0.9.0
[0.1.0]: https://github.com/larapy-lab/framework/releases/tag/v0.1.0
