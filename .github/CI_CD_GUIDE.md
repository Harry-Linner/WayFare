# CI/CD Quick Reference Guide

## 🚀 Quick Start

### Before Pushing Code

Run these commands to ensure your code will pass CI:

```bash
# 1. Format code
black wayfare/ nanobot/ tests/

# 2. Run linter
ruff check --fix wayfare/ nanobot/ tests/

# 3. Run tests
pytest tests/ -v

# 4. Check coverage (optional)
pytest tests/ --cov=wayfare --cov-report=term
```

## 📋 CI/CD Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Push/Pull Request                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────┐                    ┌──────────────────┐
│   Test Job    │                    │ Code Quality Job │
│               │                    │                  │
│ • Unit Tests  │                    │ • Black          │
│ • PBT Tests   │                    │ • Ruff           │
│ • Integration │                    │ • mypy           │
│ • Coverage    │                    │ • Pylint         │
└───────────────┘                    └──────────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
                ┌───────────────┐
                │  CI Success   │
                └───────────────┘
```

## 🧪 Test Categories

### Unit Tests
**What**: Test individual functions and classes in isolation
**Location**: `tests/` and `tests/wayfare/`
**Run**: `pytest tests/ --ignore=tests/wayfare/test_serialization_roundtrip.py`

### Property-Based Tests (PBT)
**What**: Test properties that should hold for all inputs using Hypothesis
**Location**: `tests/wayfare/test_serialization_roundtrip.py`
**Run**: `pytest tests/wayfare/test_serialization_roundtrip.py`

### Integration Tests
**What**: Test multiple components working together
**Location**: `tests/wayfare/*integration*.py`
**Run**: `pytest tests/wayfare/ -k "integration"`
**Requires**: Qdrant running on localhost:6333

## 🛠️ Code Quality Tools

### Black (Code Formatter)
```bash
# Check formatting
black --check wayfare/ nanobot/ tests/

# Auto-format
black wayfare/ nanobot/ tests/
```

**Status in CI**: ❌ Blocking (fails CI if not formatted)

### Ruff (Fast Linter)
```bash
# Check issues
ruff check wayfare/ nanobot/ tests/

# Auto-fix issues
ruff check --fix wayfare/ nanobot/ tests/
```

**Status in CI**: ❌ Blocking (fails CI if errors found)

### mypy (Type Checker)
```bash
# Check types
mypy wayfare/ --ignore-missing-imports --no-strict-optional
```

**Status in CI**: ⚠️ Non-blocking (warnings only)

### Pylint (Additional Linting)
```bash
# Check code quality
pylint wayfare/ --disable=C0111,R0903,W0212,C0103 --max-line-length=100
```

**Status in CI**: ⚠️ Non-blocking (warnings only)

## 📊 Code Coverage

### Generate Coverage Report
```bash
# Terminal report
pytest tests/ --cov=wayfare --cov-report=term

# HTML report (opens in browser)
pytest tests/ --cov=wayfare --cov-report=html
open htmlcov/index.html
```

### Coverage Targets
- **Minimum**: 70% (recommended)
- **Good**: 80%+
- **Excellent**: 90%+

## 🐳 Running Integration Tests Locally

### Start Qdrant
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant:latest

# Or using Docker Compose (if available)
docker-compose up qdrant
```

### Run Integration Tests
```bash
# Set environment variable
export QDRANT_URL=http://localhost:6333

# Run tests
pytest tests/wayfare/ -k "integration" -v
```

## 🔧 Common Issues and Solutions

### Issue: Black formatting fails
**Solution**: Run `black wayfare/ nanobot/ tests/` to auto-format

### Issue: Ruff linting errors
**Solution**: Run `ruff check --fix wayfare/ nanobot/ tests/` to auto-fix

### Issue: Tests fail with "Qdrant connection error"
**Solution**: Start Qdrant service: `docker run -p 6333:6333 qdrant/qdrant:latest`

### Issue: Import errors in tests
**Solution**: Install dev dependencies: `pip install -r requirements-dev.txt`

### Issue: mypy type errors
**Solution**: These are non-blocking in CI, but you can fix them by adding type hints

### Issue: Coverage too low
**Solution**: Add more tests for uncovered code paths

## 📝 Pre-Commit Checklist

Before pushing code, ensure:

- [ ] Code is formatted with Black
- [ ] Ruff linting passes
- [ ] All tests pass locally
- [ ] New code has tests
- [ ] Coverage hasn't decreased significantly
- [ ] No sensitive data in commits
- [ ] Commit messages are descriptive

## 🎯 CI/CD Best Practices

### 1. Write Tests First
- Write tests before or alongside code
- Aim for high coverage of critical paths
- Use property-based tests for complex logic

### 2. Keep Tests Fast
- Mock external services when possible
- Use fixtures for common setup
- Parallelize tests when appropriate

### 3. Fix Failing Tests Immediately
- Don't push code with failing tests
- Don't disable tests to make CI pass
- Investigate and fix root causes

### 4. Monitor CI Performance
- Check CI run times regularly
- Optimize slow tests
- Use caching effectively

### 5. Keep Dependencies Updated
- Regularly update `requirements-dev.txt`
- Test with latest Python versions
- Monitor security advisories

## 🔐 Secrets Management

### Required Secrets
- `CODECOV_TOKEN`: For coverage reporting (optional but recommended)

### Adding Secrets
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secret name and value
4. Secrets are encrypted and not visible in logs

## 📈 Monitoring CI/CD

### Check CI Status
- **GitHub Actions tab**: View all workflow runs
- **Pull Request checks**: See status before merging
- **Branch protection**: Require CI to pass before merge

### CI Metrics to Track
- **Build time**: Should be < 5 minutes
- **Test pass rate**: Should be > 95%
- **Coverage trend**: Should be stable or increasing
- **Flaky tests**: Identify and fix tests that fail intermittently

## 🚨 Emergency Procedures

### CI is Broken on Main Branch
1. Identify the breaking commit
2. Create hotfix branch
3. Fix the issue
4. Create PR with fix
5. Merge after CI passes

### All Tests Failing
1. Check if it's an infrastructure issue (Qdrant, GitHub Actions)
2. Check recent dependency updates
3. Verify Python version compatibility
4. Check for breaking changes in dependencies

### Coverage Dropped Significantly
1. Identify which files lost coverage
2. Add tests for uncovered code
3. Review if code deletion was intentional

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Codecov Documentation](https://docs.codecov.com/)

## 💡 Tips and Tricks

### Speed Up Local Testing
```bash
# Run only failed tests
pytest --lf

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run specific test file
pytest tests/wayfare/test_db.py

# Run specific test function
pytest tests/wayfare/test_db.py::test_save_document
```

### Debug Failing Tests
```bash
# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Show full traceback
pytest --tb=long
```

### Check What Will Run in CI
```bash
# Simulate CI locally
black --check wayfare/ nanobot/ tests/ && \
ruff check wayfare/ nanobot/ tests/ && \
pytest tests/ -v
```
