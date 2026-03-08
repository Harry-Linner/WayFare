# Development Guide

This guide covers development environment setup, coding standards, testing practices, and contribution guidelines for WayFare MVP Backend.

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- (Optional) Node.js 18+ for WhatsApp bridge

### Initial Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd wayfare-mvp-backend
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install dependencies**:
```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

4. **Download ONNX model**:
```bash
# The setup script handles this automatically
bash setup.sh  # Linux/Mac
# or
setup.bat  # Windows
```

5. **Start Qdrant**:
```bash
docker-compose up -d
```

6. **Set environment variables**:
```bash
export SILICONFLOW_API_KEY=your_api_key_here
export WAYFARE_DB_PATH=.wayfare/wayfare.db
```

### IDE Configuration

#### VS Code

Recommended extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Mypy Type Checker (ms-python.mypy-type-checker)

Settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true
}
```

#### PyCharm

1. Set Python interpreter to the virtual environment
2. Enable Black formatter: Settings → Tools → Black
3. Enable pytest: Settings → Tools → Python Integrated Tools → Testing → pytest

## Project Structure

```
wayfare/
├── __init__.py              # Package initialization
├── main.py                  # Entry point
├── ipc.py                   # IPC handler
├── document_parser.py       # Document parsing
├── annotation_generator.py  # Annotation generation
├── behavior_analyzer.py     # Behavior analysis
├── embedding.py             # Embedding service
├── vector_store.py          # Qdrant client
├── llm_provider.py          # LLM provider wrapper
├── context_builder.py       # Context builder wrapper
├── db.py                    # SQLite database
├── config.py                # Configuration management
├── logging.py               # Logging setup
├── errors.py                # Custom exceptions
└── models/                  # Data models
    └── __init__.py
```

## Coding Standards

### Python Style Guide

Follow PEP 8 with these specific guidelines:

1. **Line length**: Maximum 100 characters
2. **Imports**: Group in order: standard library, third-party, local
3. **Type hints**: Use type hints for all function signatures
4. **Docstrings**: Use Google-style docstrings

Example:
```python
from typing import List, Optional
import asyncio

from wayfare.errors import DocumentParseError


async def parse_document(
    path: str,
    chunk_size: int = 300
) -> List[DocumentSegment]:
    """Parse a document and return segments.
    
    Args:
        path: Path to the document file
        chunk_size: Maximum size of each chunk in characters
        
    Returns:
        List of document segments
        
    Raises:
        DocumentParseError: If parsing fails
    """
    # Implementation
    pass
```

### Code Formatting

Use Black for code formatting:
```bash
black wayfare/ tests/
```

### Linting

Use pylint for linting:
```bash
pylint wayfare/ tests/
```

### Type Checking

Use mypy for type checking:
```bash
mypy wayfare/
```

## Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest fixtures
└── wayfare/
    ├── test_config.py       # Unit tests
    ├── test_db.py
    ├── test_embedding.py
    ├── test_vector_store.py
    ├── test_document_parser.py
    ├── test_annotation_generator.py
    ├── test_behavior_analyzer.py
    ├── test_ipc.py
    ├── test_*_integration.py  # Integration tests
    └── test_*_property.py     # Property-based tests
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/wayfare/test_db.py

# Specific test function
pytest tests/wayfare/test_db.py::test_save_document

# With coverage
pytest --cov=wayfare --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Writing Tests

#### Unit Tests

```python
import pytest
from wayfare.db import SQLiteDB


@pytest.mark.asyncio
async def test_save_document(tmp_path):
    """Test saving a document to the database."""
    db_path = tmp_path / "test.db"
    db = SQLiteDB(str(db_path))
    await db.initialize()
    
    doc = {
        "hash": "test_hash",
        "path": "/test/doc.pdf",
        "status": "completed",
        "version_hash": "v1"
    }
    
    await db.save_document(doc)
    result = await db.get_document("test_hash")
    
    assert result is not None
    assert result["hash"] == "test_hash"
    assert result["status"] == "completed"
```

#### Integration Tests

```python
import pytest
from wayfare.ipc import IPCHandler
from wayfare.document_parser import DocumentParser


@pytest.mark.asyncio
async def test_parse_integration(tmp_path, sample_pdf):
    """Test complete parse flow from IPC to database."""
    # Setup
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Initialize components
    ipc_handler = IPCHandler(workspace)
    
    # Send parse request
    request = {
        "id": "test-1",
        "seq": 1,
        "method": "parse",
        "params": {"path": str(sample_pdf)}
    }
    
    response = await ipc_handler.handle_request(request)
    
    # Verify response
    assert response["success"] is True
    assert "docHash" in response["data"]
```

#### Property-Based Tests

```python
from hypothesis import given, strategies as st
import pytest


@given(
    text=st.text(min_size=100, max_size=1000),
    chunk_size=st.integers(min_value=200, max_value=500)
)
def test_chunk_text_property(text, chunk_size):
    """Property: All chunks should be within size constraints."""
    from wayfare.document_parser import DocumentParser
    
    parser = DocumentParser(None, None, None)
    parser.chunk_size = chunk_size
    
    chunks = parser.chunk_text(text, page=0)
    
    for chunk in chunks:
        assert 0 < len(chunk) <= chunk_size + 100  # Allow some overflow
```

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
import pytest
from pathlib import Path


@pytest.fixture
def tmp_workspace(tmp_path):
    """Create a temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def sample_pdf():
    """Path to a sample PDF file."""
    return Path("tests/fixtures/sample.pdf")


@pytest.fixture
async def test_db(tmp_path):
    """Create a test database."""
    from wayfare.db import SQLiteDB
    
    db_path = tmp_path / "test.db"
    db = SQLiteDB(str(db_path))
    await db.initialize()
    return db
```

## Debugging

### Logging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export WAYFARE_LOG_LEVEL=DEBUG
```

### Interactive Debugging

Use Python debugger:
```python
import pdb; pdb.set_trace()
```

Or use VS Code debugger with launch configuration:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Main",
      "type": "python",
      "request": "launch",
      "module": "wayfare.main",
      "args": ["--workspace", "${workspaceFolder}/.wayfare"],
      "console": "integratedTerminal"
    }
  ]
}
```

## Common Development Tasks

### Adding a New Component

1. Create the module file in `wayfare/`
2. Define the class with type hints
3. Add docstrings
4. Create corresponding test file in `tests/wayfare/`
5. Write unit tests
6. Update `wayfare/__init__.py` if needed

### Adding a New IPC Method

1. Add method handler in `wayfare/ipc.py`:
```python
async def handle_new_method(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle new_method request."""
    # Implementation
    return {"result": "success"}
```

2. Register in `_route_request`:
```python
elif request.method == "new_method":
    data = await self.handle_new_method(request.params)
```

3. Add tests in `tests/wayfare/test_ipc.py`
4. Update API documentation in `API.md`

### Updating Dependencies

1. Update `requirements.txt` or `requirements-dev.txt`
2. Reinstall:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```
3. Test thoroughly
4. Update `DEPENDENCIES.md` if needed

## Performance Profiling

### CPU Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Profiling

```bash
pip install memory_profiler

python -m memory_profiler wayfare/main.py
```

## Troubleshooting

### Common Issues

**Issue**: Qdrant connection error
```
Solution: Ensure Qdrant is running: docker-compose up -d
```

**Issue**: ONNX model not found
```
Solution: Download model: bash setup.sh
```

**Issue**: Import errors
```
Solution: Ensure virtual environment is activated and dependencies installed
```

**Issue**: Tests fail with database locked
```
Solution: Close any open database connections or use tmp_path fixture
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and commit: `git commit -am 'Add my feature'`
4. Write tests for your changes
5. Ensure all tests pass: `pytest`
6. Format code: `black wayfare/ tests/`
7. Push to your fork: `git push origin feature/my-feature`
8. Create a Pull Request

### Commit Message Guidelines

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Build/tooling changes

Example:
```
feat: add support for DOCX document parsing

- Implement DOCX parser using python-docx
- Add tests for DOCX parsing
- Update documentation
```

## Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Hypothesis Property Testing](https://hypothesis.readthedocs.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
