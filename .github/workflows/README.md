# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing and code quality checks.

## Workflows

### test.yml - Test and Quality Checks

This workflow runs on every push and pull request to `main` and `develop` branches.

#### Jobs

##### 1. Test Job

Runs the complete test suite across multiple Python versions.

**Matrix Strategy:**
- Python 3.11
- Python 3.12

**Services:**
- Qdrant vector database (required for integration tests)

**Steps:**
1. **Checkout code** - Gets the repository code
2. **Set up Python** - Installs the specified Python version with pip caching
3. **Cache pip dependencies** - Caches pip packages for faster builds
4. **Install dependencies** - Installs all dev dependencies from `requirements-dev.txt`
5. **Run unit tests** - Executes all unit tests (excluding property-based tests)
6. **Run property-based tests** - Executes Hypothesis property-based tests separately
7. **Run integration tests** - Executes integration tests with Qdrant service
8. **Generate coverage report** - Creates code coverage reports in XML and terminal formats
9. **Upload coverage to Codecov** - Uploads coverage data to Codecov (requires `CODECOV_TOKEN` secret)

**Environment Variables:**
- `QDRANT_URL`: Set to `http://localhost:6333` for integration tests

##### 2. Code Quality Job

Runs code quality checks and linting tools.

**Steps:**
1. **Checkout code** - Gets the repository code
2. **Set up Python** - Installs Python 3.11 with pip caching
3. **Cache pip dependencies** - Caches pip packages for faster builds
4. **Install dependencies** - Installs all dev dependencies
5. **Check code formatting with Black** - Verifies code follows Black formatting standards
6. **Run Ruff linter** - Fast Python linter for code quality
7. **Run type checking with mypy** - Static type checking (non-blocking)
8. **Run Pylint** - Additional linting checks (non-blocking)

## Configuration

### Required Secrets

To enable code coverage reporting, add the following secret to your GitHub repository:

- `CODECOV_TOKEN`: Your Codecov upload token (get it from https://codecov.io)

**How to add secrets:**
1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add `CODECOV_TOKEN` with your token value

### Caching Strategy

The workflow uses GitHub Actions caching to speed up builds:

- **Pip cache**: Caches Python packages between runs
- **Cache key**: Based on `requirements-dev.txt` hash
- **Restore keys**: Falls back to most recent cache if exact match not found

This reduces build time from ~2-3 minutes to ~30-60 seconds on cache hits.

## Test Organization

### Unit Tests
- Location: `tests/` and `tests/wayfare/`
- Excludes: Property-based tests
- Command: `pytest tests/ -v --tb=short --ignore=tests/wayfare/test_serialization_roundtrip.py`

### Property-Based Tests
- Location: `tests/wayfare/test_serialization_roundtrip.py`
- Framework: Hypothesis
- Command: `pytest tests/wayfare/test_serialization_roundtrip.py -v --tb=short`

### Integration Tests
- Location: `tests/wayfare/` (files with "integration" in name)
- Requires: Qdrant service
- Command: `pytest tests/wayfare/ -v --tb=short -k "integration"`

## Code Quality Tools

### Black
- **Purpose**: Code formatting
- **Config**: Default Black style
- **Behavior**: Fails CI if code is not formatted
- **Fix locally**: `black wayfare/ nanobot/ tests/`

### Ruff
- **Purpose**: Fast Python linter
- **Config**: Defined in `pyproject.toml`
- **Behavior**: Fails CI if linting errors found
- **Fix locally**: `ruff check --fix wayfare/ nanobot/ tests/`

### mypy
- **Purpose**: Static type checking
- **Config**: `--ignore-missing-imports --no-strict-optional`
- **Behavior**: Non-blocking (continue-on-error: true)
- **Check locally**: `mypy wayfare/ --ignore-missing-imports --no-strict-optional`

### Pylint
- **Purpose**: Additional code quality checks
- **Config**: Disables some rules (C0111, R0903, W0212, C0103)
- **Behavior**: Non-blocking (continue-on-error: true)
- **Check locally**: `pylint wayfare/ --disable=C0111,R0903,W0212,C0103 --max-line-length=100`

## Running Tests Locally

### Install Dependencies
```bash
pip install -r requirements-dev.txt
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=wayfare --cov=nanobot --cov-report=html
```

### Run Code Quality Checks
```bash
# Format code
black wayfare/ nanobot/ tests/

# Lint code
ruff check wayfare/ nanobot/ tests/

# Type check
mypy wayfare/ --ignore-missing-imports --no-strict-optional

# Pylint
pylint wayfare/ --disable=C0111,R0903,W0212,C0103 --max-line-length=100
```

### Start Qdrant for Integration Tests
```bash
docker run -p 6333:6333 qdrant/qdrant:latest
```

## Troubleshooting

### Tests Fail Locally But Pass in CI
- Ensure you have the latest dependencies: `pip install -r requirements-dev.txt --upgrade`
- Check Python version matches CI (3.11 or 3.12)
- Ensure Qdrant is running for integration tests

### Coverage Upload Fails
- Verify `CODECOV_TOKEN` secret is set correctly
- Check Codecov service status
- Note: Coverage upload failure doesn't fail the CI (fail_ci_if_error: false)

### Cache Issues
- GitHub Actions caches are immutable once created
- If dependencies change, the cache key will change automatically
- Manual cache clearing: Go to Actions → Caches → Delete old caches

## Performance Optimization

### Current Build Times
- **With cache hit**: ~30-60 seconds
- **Without cache**: ~2-3 minutes

### Optimization Strategies
1. **Pip caching**: Reduces dependency installation time
2. **Matrix strategy**: Runs Python versions in parallel
3. **Separate jobs**: Test and quality checks run in parallel
4. **Continue-on-error**: Non-critical checks don't block the pipeline

## Future Enhancements

Potential improvements for the CI/CD pipeline:

1. **Add deployment workflow** - Automate releases to PyPI
2. **Add security scanning** - Integrate Snyk or Dependabot
3. **Add performance benchmarks** - Track performance regressions
4. **Add documentation builds** - Auto-generate and deploy docs
5. **Add Docker image builds** - Build and push container images
6. **Add release automation** - Auto-generate changelogs and releases
