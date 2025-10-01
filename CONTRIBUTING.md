# Contributing to Substack MCP Server

Thank you for considering contributing to the Substack MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.10 or higher (Python 3.11 recommended)
- Git
- Claude Desktop (for testing MCP integration)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/substack_mcp.git
cd substack_mcp

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests to verify setup
pytest
```

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

1. **Clear title** describing the issue
2. **Detailed description** of the problem
3. **Steps to reproduce** the issue
4. **Expected behavior** vs. actual behavior
5. **Environment details** (OS, Python version, MCP SDK version)
6. **Error messages** or stack traces if applicable

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:

1. **Clear title** describing the enhancement
2. **Use case** - why this would be valuable
3. **Proposed solution** or approach
4. **Alternatives considered**

### Pull Requests

We actively welcome pull requests!

#### Before You Start

1. Check existing issues and PRs to avoid duplicates
2. Create an issue to discuss major changes first
3. Fork the repository and create a branch

#### PR Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**:
   - Write clear, readable code
   - Follow existing code style
   - Add/update tests as needed
   - Update documentation if needed

3. **Test your changes**:
   ```bash
   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=substack_mcp

   # Run specific tests
   pytest tests/test_client.py -v
   ```

4. **Test MCP integration**:
   - Configure in Claude Desktop
   - Test all affected MCP tools
   - Verify stdio transport works correctly

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**:
   - Provide clear description of changes
   - Reference related issues
   - Describe testing performed

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where possible
- Write docstrings for functions and classes
- Keep functions focused and single-purpose

### Code Organization

```python
# Good: Clear, typed, documented
def fetch_posts(handle: str, limit: int = 10) -> list[PostSummary]:
    """Fetch recent posts from a Substack publication.

    Args:
        handle: The Substack publication handle
        limit: Maximum number of posts to fetch (default: 10)

    Returns:
        List of PostSummary objects

    Raises:
        HTTPError: If the request fails
    """
    # Implementation here
    pass
```

### Testing

- Write tests for all new features
- Maintain or improve test coverage
- Use fixtures for test data
- Mock external HTTP requests (use `respx`)

```python
# Example test structure
import pytest
from substack_mcp.client import SubstackPublicClient

def test_fetch_posts_success(mock_http):
    """Test successful post fetching."""
    client = SubstackPublicClient()
    posts = client.fetch_feed("testhandle", limit=5)
    assert len(posts) == 5
    assert all(isinstance(p, PostSummary) for p in posts)
```

### MCP Tools

When adding new MCP tools:

1. **Define schema** in `@server.list_tools()`:
   ```python
   Tool(
       name="your_tool",
       description="Clear description of what it does",
       inputSchema={
           "type": "object",
           "properties": {
               "param": {
                   "type": "string",
                   "description": "Parameter description"
               }
           },
           "required": ["param"]
       }
   )
   ```

2. **Implement handler** in `@server.call_tool()`:
   ```python
   if name == "your_tool":
       param = arguments.get("param")
       result = your_function(param)
       return create_text_result(json.dumps(result, indent=2))
   ```

3. **Add tests** for the tool
4. **Update README.md** with tool documentation

## Project Structure

```
substack_mcp/
├── src/substack_mcp/      # Source code
│   ├── client.py          # HTTP client
│   ├── models.py          # Pydantic models
│   ├── parsers.py         # Content parsers
│   ├── analysis.py        # Analytics engine
│   ├── cache.py           # Caching layer
│   ├── server.py          # MCP server
│   └── settings.py        # Configuration
├── tests/                 # Test suite
│   ├── fixtures/          # Test data
│   └── test_*.py          # Test modules
├── scripts/               # Utility scripts
├── README.md              # User documentation
├── CLAUDE.md              # Developer documentation
└── CONTRIBUTING.md        # This file
```

## Areas for Contribution

### High Priority

- [ ] Persistent storage (SQLite) for cached content
- [ ] Additional analytics (topic modeling, entity extraction)
- [ ] Performance optimizations
- [ ] More comprehensive test coverage
- [ ] Documentation improvements

### Good First Issues

- Bug fixes for existing issues
- Documentation improvements
- Test coverage improvements
- Example workflows and use cases

### Advanced

- Background worker for scheduled crawls
- Advanced NLP/ML features
- Custom analytics pipelines
- Performance profiling and optimization

## Testing Guidelines

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test MCP tool integration
3. **Mock Tests**: Use `respx` to mock HTTP calls

### Running Tests

```bash
# All tests
pytest

# Specific module
pytest tests/test_client.py

# With coverage report
pytest --cov=substack_mcp --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Writing Good Tests

```python
# Good test characteristics:
# 1. Clear test name
# 2. Single concern
# 3. Arrange-Act-Assert pattern
# 4. Mock external dependencies

def test_parse_feed_with_valid_rss(sample_rss_fixture):
    """Test RSS feed parsing with valid feed."""
    # Arrange
    feed_content = sample_rss_fixture

    # Act
    posts = parse_feed(feed_content, "https://test.substack.com/")

    # Assert
    assert len(posts) > 0
    assert all(isinstance(p, PostSummary) for p in posts)
```

## Documentation

### Code Documentation

- Use docstrings for all public functions/classes
- Include parameter types and return types
- Document exceptions that can be raised
- Provide usage examples for complex functions

### User Documentation

When adding features, update:
- `README.md` - User-facing documentation
- `CLAUDE.md` - Developer/Claude Code guidance
- Tool descriptions in MCP server

## Questions?

If you have questions about contributing:

1. Check existing documentation (README.md, CLAUDE.md)
2. Search existing issues
3. Create a new issue with the `question` label
4. Be specific about what you're trying to accomplish

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Project acknowledgments
- Release notes (for significant contributions)

Thank you for contributing to Substack MCP Server! Your efforts help make this tool better for everyone.
