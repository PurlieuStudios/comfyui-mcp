# Contributing to ComfyUI MCP Server

Thank you for your interest in contributing to the ComfyUI MCP Server! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Getting Help](#getting-help)

---

## Code of Conduct

This project and everyone participating in it is governed by our commitment to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Our Standards

- **Be Respectful**: Treat everyone with respect and kindness
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Collaborative**: Work together towards common goals
- **Be Patient**: Remember that everyone was a beginner once

---

## How Can I Contribute?

There are many ways to contribute to this project:

### Reporting Bugs

If you find a bug, please create an issue on GitHub with:

- **Clear title and description**
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (Python version, OS, ComfyUI version)
- **Error messages** and stack traces if applicable

### Suggesting Enhancements

We welcome feature requests and enhancement suggestions! Please create an issue with:

- **Clear use case** - Why is this enhancement useful?
- **Proposed solution** - How might this work?
- **Alternatives considered** - What other approaches did you think about?

### Contributing Code

We love code contributions! See the [Development Workflow](#development-workflow) section below for detailed instructions.

### Improving Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples or use cases
- Improve API documentation
- Write tutorials or guides

### Writing Tests

Help improve test coverage by:

- Adding tests for uncovered code
- Writing integration tests
- Creating test fixtures
- Improving test documentation

---

## Development Setup

### Prerequisites

- **Python 3.10 or higher**
- **Git**
- **ComfyUI** installed and running (for integration tests)
- **Visual Studio Code** or your preferred IDE (optional)

### Initial Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/comfyui-mcp.git
   cd comfyui-mcp
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/PurlieuStudios/comfyui-mcp.git
   ```

4. **Create a virtual environment**:
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

5. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

6. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

7. **Verify installation**:
   ```bash
   # Run tests
   pytest tests/ -v

   # Type check
   mypy src/

   # Lint check
   ruff check src/ tests/
   ```

---

## Development Workflow

We follow **Test-Driven Development (TDD)** and strict quality standards.

### TDD Workflow (RED → GREEN → REFACTOR)

1. **RED Phase**: Write a failing test
   ```bash
   # Create test first (it should fail)
   pytest tests/test_my_feature.py -v
   ```

2. **GREEN Phase**: Implement minimum code to pass
   ```python
   # Implement the feature
   # Run tests until they pass
   pytest tests/test_my_feature.py -v
   ```

3. **REFACTOR Phase**: Clean up and optimize
   ```python
   # Improve code quality
   # Ensure tests still pass
   pytest tests/ -v
   ```

### Step-by-Step Contribution

1. **Sync with upstream**:
   ```bash
   git checkout master
   git pull upstream master
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/issue-XX-descriptive-name
   ```

3. **Write tests first** (TDD):
   ```bash
   # Create test file
   # tests/test_my_feature.py

   # Run test (should fail)
   pytest tests/test_my_feature.py -v
   ```

4. **Implement the feature**:
   ```python
   # Write code in src/comfyui_mcp/
   # Follow coding standards
   # Add type hints and docstrings
   ```

5. **Run all quality checks**:
   ```bash
   # Tests with coverage
   pytest tests/ -v --cov=comfyui_mcp --cov-report=term-missing

   # Type checking
   mypy src/

   # Linting
   ruff check src/ tests/

   # Formatting
   ruff format src/ tests/
   ```

6. **Update documentation**:
   - Add/update docstrings
   - Update README.md if needed
   - Update relevant docs in `docs/`

7. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(module): descriptive commit message

   - Detail what was changed
   - Why the change was made
   - Reference any related issues

   Fixes #XX"
   ```

8. **Push to your fork**:
   ```bash
   git push origin feature/issue-XX-descriptive-name
   ```

9. **Create a Pull Request** on GitHub

---

## Testing

### Test Requirements

- **Minimum Coverage**: 80% (we maintain 95%+)
- **All tests must pass**: No exceptions
- **Type checking must pass**: 0 mypy errors
- **Linting must pass**: 0 ruff errors

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=comfyui_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_comfyui_client.py -v

# Run tests matching a pattern
pytest tests/ -v -k "test_workflow"

# Run tests in parallel (faster)
pytest tests/ -v -n auto
```

### Writing Tests

Follow these guidelines when writing tests:

1. **Use descriptive names**:
   ```python
   def test_submit_workflow_returns_prompt_id():
       """Test that submit_workflow returns a valid prompt ID."""
       pass
   ```

2. **Follow AAA pattern** (Arrange, Act, Assert):
   ```python
   def test_example():
       # Arrange - Set up test data
       config = ComfyUIConfig(url="http://localhost:8188")
       client = ComfyUIClient(config)

       # Act - Perform the action
       result = await client.health_check()

       # Assert - Verify the result
       assert result is True
   ```

3. **Test edge cases**:
   - Empty inputs
   - Invalid inputs
   - Boundary conditions
   - Error conditions

4. **Use fixtures** for common setup:
   ```python
   @pytest.fixture
   def comfyui_client():
       config = ComfyUIConfig(url="http://localhost:8188")
       return ComfyUIClient(config)
   ```

5. **Mock external dependencies**:
   ```python
   @pytest.mark.asyncio
   async def test_with_mock(aiohttp_client):
       # Mock ComfyUI server responses
       pass
   ```

### Test Organization

```
tests/
├── test_comfyui_client.py      # Client tests
├── test_models.py              # Model validation tests
├── test_config_validation.py   # Config tests
├── test_config_env.py          # Environment config tests
├── test_retry.py               # Retry logic tests
├── test_exceptions.py          # Exception tests
└── test_logging_integration.py # Logging tests
```

---

## Code Style

### Python Style Guide

We follow **PEP 8** with these tools:

- **Ruff**: Fast linting and formatting
- **Black**: Code formatter (via ruff)
- **mypy**: Static type checking (strict mode)

### Key Conventions

1. **Type Hints**: Required on all functions
   ```python
   def process_workflow(workflow: WorkflowPrompt) -> str:
       """Process a workflow and return the prompt ID."""
       pass
   ```

2. **Docstrings**: Required on all public methods/classes
   ```python
   async def health_check(self) -> bool:
       """
       Check if the ComfyUI server is accessible and responding.

       Returns:
           bool: True if server is healthy, False otherwise.

       Example:
           >>> async with ComfyUIClient(config) as client:
           ...     is_healthy = await client.health_check()
       """
       pass
   ```

3. **Pydantic Models**: All data structures
   ```python
   from pydantic import BaseModel, Field

   class WorkflowPrompt(BaseModel):
       """Represents a ComfyUI workflow prompt."""
       prompt: dict[str, Any]
       client_id: str | None = None
   ```

4. **Imports**: Organized and grouped
   ```python
   # Standard library
   import asyncio
   from typing import Any

   # Third-party
   import aiohttp
   from pydantic import BaseModel

   # Local
   from comfyui_mcp.exceptions import ComfyUIError
   from comfyui_mcp.models import WorkflowPrompt
   ```

5. **Line Length**: Maximum 88 characters (Black style)

6. **Naming Conventions**:
   - **Classes**: PascalCase (e.g., `ComfyUIClient`)
   - **Functions/Variables**: snake_case (e.g., `submit_workflow`)
   - **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)
   - **Private**: Leading underscore (e.g., `_internal_method`)

### Code Quality Checks

Run these before committing:

```bash
# Type checking (strict mode)
mypy src/

# Linting
ruff check src/ tests/

# Format code
ruff format src/ tests/

# All checks via pre-commit
pre-commit run --all-files
```

### Pre-commit Hooks

Our pre-commit hooks automatically check:

- Trailing whitespace
- End of file fixes
- YAML/JSON/TOML syntax
- Large files
- Merge conflicts
- Debug statements
- Code formatting (ruff)
- Type checking (mypy)

---

## Git Workflow

### Branch Naming

Use descriptive branch names:

```bash
feature/issue-XX-short-description   # New features
bugfix/issue-XX-short-description    # Bug fixes
docs/issue-XX-short-description      # Documentation
refactor/short-description           # Refactoring
test/short-description               # Test improvements
```

### Commit Messages

Follow the **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `style`: Code style (formatting, etc.)
- `chore`: Maintenance tasks

**Example**:
```bash
git commit -m "feat(client): add retry logic with exponential backoff

Implemented automatic retry for failed API requests with exponential
backoff strategy. This improves reliability when ComfyUI server is
temporarily unavailable or under load.

- Added retry_with_backoff decorator
- Configurable max attempts and backoff multiplier
- Unit tests with 100% coverage

Fixes #42"
```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream master into your master
git checkout master
git merge upstream/master

# Push updates to your fork
git push origin master

# Rebase your feature branch
git checkout feature/my-feature
git rebase master
```

---

## Pull Request Process

### Before Submitting

1. ✅ **All tests pass**: `pytest tests/ -v --cov`
2. ✅ **Type checking passes**: `mypy src/`
3. ✅ **Linting passes**: `ruff check src/ tests/`
4. ✅ **Code is formatted**: `ruff format src/ tests/`
5. ✅ **Coverage is 80%+** (aim for 95%+)
6. ✅ **Documentation updated**: Docstrings, README, etc.
7. ✅ **CHANGELOG updated** (if applicable)
8. ✅ **Commits are clean**: Squash if needed

### PR Description Template

```markdown
## Summary

Brief description of the changes and motivation.

## Changes Made

- Change 1
- Change 2
- Change 3

## Testing

How was this tested? What scenarios were covered?

## Screenshots (if applicable)

Add screenshots for UI changes.

## Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues

Fixes #XX
Closes #YY
```

### PR Review Process

1. **Automated checks run**: CI/CD pipeline
2. **Code review**: Maintainer reviews your code
3. **Feedback addressed**: Make requested changes
4. **Approval**: PR is approved
5. **Merge**: Squash and merge to master

### PR Guidelines

- **Keep PRs focused**: One feature/fix per PR
- **Keep PRs small**: Easier to review
- **Write clear descriptions**: Help reviewers understand
- **Respond to feedback**: Be open to suggestions
- **Be patient**: Reviews may take time

---

## Project Structure

Understanding the project structure will help you contribute effectively:

```
comfyui-mcp/
├── src/
│   └── comfyui_mcp/           # Main package
│       ├── __init__.py        # Public API exports
│       ├── server.py          # MCP server (future)
│       ├── comfyui_client.py  # ComfyUI API client
│       ├── models.py          # Pydantic models
│       ├── exceptions.py      # Custom exceptions
│       ├── retry.py           # Retry logic
│       └── ...
├── tests/                     # Test suite
│   ├── test_comfyui_client.py
│   ├── test_models.py
│   └── ...
├── docs/                      # Documentation
│   ├── API.md                 # API reference
│   ├── CONFIGURATION.md       # Config guide
│   ├── COMFYUI_API.md        # ComfyUI API
│   └── MCP_TOOLS.md          # MCP tools
├── examples/                  # Example code (future)
│   └── config/               # Config examples
├── workflows/                 # Workflow templates (future)
├── .github/                   # GitHub config
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline
├── pyproject.toml            # Package configuration
├── README.md                 # User documentation
├── CLAUDE.md                 # AI assistant context
├── CONTRIBUTING.md           # This file
└── LICENSE                   # MIT License
```

### Key Files

- **`pyproject.toml`**: Package metadata, dependencies, tool configs
- **`src/comfyui_mcp/__init__.py`**: Public API exports
- **`src/comfyui_mcp/models.py`**: All Pydantic models
- **`tests/`**: Mirror structure of `src/comfyui_mcp/`

---

## Documentation

### Documentation Types

1. **Code Documentation**: Docstrings in code
2. **API Documentation**: `docs/API.md`
3. **User Guides**: README, configuration guides
4. **Developer Docs**: This CONTRIBUTING.md

### Writing Documentation

- **Be clear and concise**
- **Provide examples**
- **Update when code changes**
- **Use consistent formatting**

### Documentation Standards

**Docstring Format**:
```python
def function_name(param1: str, param2: int = 10) -> bool:
    """
    Brief one-line description.

    Longer description with more details about the function's behavior,
    edge cases, and important notes.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)

    Returns:
        bool: Description of return value

    Raises:
        ValueError: When invalid input
        ComfyUIError: When API call fails

    Example:
        >>> result = function_name("test", 20)
        >>> print(result)
        True
    """
    pass
```

---

## Getting Help

### Resources

- **[GitHub Issues](https://github.com/PurlieuStudios/comfyui-mcp/issues)**: Bug reports and feature requests
- **[GitHub Discussions](https://github.com/PurlieuStudios/comfyui-mcp/discussions)**: Q&A and community chat
- **[Documentation](docs/)**: Comprehensive guides and references

### Communication

- **Be respectful**: We're all here to learn and help
- **Be specific**: Provide context and details
- **Be patient**: Responses may take time

### Common Questions

**Q: How do I run tests?**
```bash
pytest tests/ -v --cov=comfyui_mcp
```

**Q: How do I fix type errors?**
```bash
mypy src/  # Shows all type errors
```

**Q: How do I format my code?**
```bash
ruff format src/ tests/
```

**Q: What Python version is supported?**
Python 3.10 or higher.

**Q: How do I update dependencies?**
Dependencies are managed in `pyproject.toml`. Update there and run:
```bash
pip install -e ".[dev]"
```

---

## Recognition

Contributors are recognized in several ways:

- **Listed in README**: Major contributors
- **Mentioned in CHANGELOG**: All contributors per release
- **GitHub profile**: Contributions shown on your profile

---

## License

By contributing to this project, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

## Thank You!

Thank you for contributing to ComfyUI MCP Server! Your contributions help make this project better for everyone.

**Questions?** Open an issue or start a discussion on GitHub.

**Ready to contribute?** Check out the [open issues](https://github.com/PurlieuStudios/comfyui-mcp/issues) and pick one to work on!

---

**Version:** 0.1.0
**Last Updated:** 2025-01-18
**Maintainer:** [Purlieu Studios](https://purlieu.studio)
