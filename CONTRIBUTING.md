# Contributing to Larapy Framework

Thank you for considering contributing to the Larapy framework! This document outlines the process for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include:

- Clear and descriptive title
- Detailed description of the issue
- Steps to reproduce the behavior
- Expected behavior
- Actual behavior
- Python version and operating system
- Framework version
- Code samples or test cases

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- Clear and descriptive title
- Detailed description of the proposed functionality
- Use cases and examples
- Why this enhancement would be useful

### Pull Requests

1. Fork the repository
2. Create a new branch from `develop`: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Write or update tests
5. Ensure all tests pass: `pytest tests/`
6. Ensure code coverage remains at 79% or higher
7. Update documentation if needed
8. Commit your changes with clear commit messages
9. Push to your fork
10. Submit a pull request to the `develop` branch

## Development Setup

```bash
git clone https://github.com/larapy-lab/framework
cd framework
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=larapy --cov-report=term
```

Run specific test file:

```bash
pytest tests/test_eloquent_model.py -v
```

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use Black for formatting: `black larapy tests`
- Use Ruff for linting: `ruff check larapy tests`
- Line length: 100 characters
- Use type hints where appropriate

### Naming Conventions

- Classes: `PascalCase` (e.g., `EloquentModel`, `QueryBuilder`)
- Functions/Methods: `snake_case` (e.g., `get_user`, `build_query`)
- Constants: `UPPER_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private methods: `_snake_case` (e.g., `_build_query`, `_process_data`)

### Documentation

- Write docstrings for all public classes and methods
- Use Google-style docstrings
- Include examples in docstrings where helpful
- Update documentation in the `larapy-lab/documentation` repository

Example docstring:

```python
def find_or_fail(self, id: int) -> Model:
    """
    Find a model by its primary key or raise an exception.
    
    Args:
        id: The primary key value to search for.
        
    Returns:
        The model instance.
        
    Raises:
        ModelNotFoundException: If no model is found.
        
    Example:
        user = User.find_or_fail(1)
    """
    pass
```

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names: `test_method_does_something_when_condition`
- Use real data in tests (no mocks unless absolutely necessary)
- Test edge cases and error conditions
- Use pytest fixtures for setup/teardown

Example test:

```python
def test_eloquent_model_creates_record_with_timestamps():
    user = User.create({
        'name': 'John Doe',
        'email': 'john@example.com',
        'password': 'secret'
    })
    
    assert user.id is not None
    assert user.name == 'John Doe'
    assert user.created_at is not None
    assert user.updated_at is not None
```

### Commit Messages

Write clear, descriptive commit messages:

- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Move cursor to..." not "Moves cursor to..."
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

Good commit messages:

```
Add HasManyThrough relationship support

Implement HasManyThrough relationship following Laravel's API.
Includes query building, eager loading, and relationship methods.

Fixes #123
```

## Architecture Guidelines

### Laravel Compatibility

- Follow Laravel's API design where applicable
- Use Laravel's naming conventions
- Maintain feature parity with Laravel 12
- Document any intentional deviations

### Framework Design Principles

- Favor composition over inheritance
- Keep classes focused and single-purpose
- Use dependency injection
- Write testable code
- Avoid static methods (except facades)
- Use async/await for I/O operations

### Adding New Features

When adding a new feature:

1. Research how Laravel implements it
2. Design the Python equivalent API
3. Write tests first (TDD approach)
4. Implement the feature
5. Ensure tests pass
6. Update documentation
7. Add examples to `examples/` directory

## Pull Request Process

1. Update README.md with details of interface changes
2. Update CHANGELOG.md following Keep a Changelog format
3. Increase version numbers following Semantic Versioning
4. The PR will be merged once you have approval from maintainers

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.9.0`
4. Push tag: `git push origin v0.9.0`
5. GitHub Actions will build and publish to PyPI

## Questions?

- Open a discussion on GitHub
- Join our Discord server
- Email: team@larapy.dev

Thank you for contributing to Larapy!
