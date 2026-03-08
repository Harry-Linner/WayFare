# CI/CD Quick Start Guide

## 🎯 For Developers: What You Need to Know

### Before You Push Code

Run this command to check if your code will pass CI:

**Linux/Mac:**
```bash
./scripts/run_ci_checks.sh
```

**Windows:**
```cmd
scripts\run_ci_checks.bat
```

### Quick Fixes

If checks fail, here's how to fix them:

```bash
# Fix code formatting
black wayfare/ nanobot/ tests/

# Fix linting issues
ruff check --fix wayfare/ nanobot/ tests/

# Run tests
pytest tests/ -v
```

## 📋 What CI Checks

### Automatic Checks on Every Push/PR

1. **Code Formatting** (Black) - Must pass ✅
2. **Code Linting** (Ruff) - Must pass ✅
3. **Type Checking** (mypy) - Warning only ⚠️
4. **Code Quality** (Pylint) - Warning only ⚠️
5. **Unit Tests** - Must pass ✅
6. **Property-Based Tests** - Must pass ✅
7. **Integration Tests** - Must pass ✅
8. **Code Coverage** - Reported 📊

### Python Versions Tested
- Python 3.11
- Python 3.12

## 🚀 First Time Setup

### 1. Install Dependencies
```bash
pip install -r requirements-dev.txt
```

### 2. Start Qdrant (for integration tests)
```bash
docker run -p 6333:6333 qdrant/qdrant:latest
```

### 3. Run Tests
```bash
pytest tests/ -v
```

## 📖 Documentation

- **Detailed Guide**: `.github/CI_CD_GUIDE.md`
- **Workflow Docs**: `.github/workflows/README.md`
- **Setup Verification**: `.github/SETUP_VERIFICATION.md`

## 🆘 Common Issues

### "Black formatting failed"
```bash
black wayfare/ nanobot/ tests/
```

### "Ruff linting failed"
```bash
ruff check --fix wayfare/ nanobot/ tests/
```

### "Tests failed - Qdrant connection error"
```bash
docker run -p 6333:6333 qdrant/qdrant:latest
```

### "Import errors"
```bash
pip install -r requirements-dev.txt
```

## ✅ Pre-Push Checklist

- [ ] Code is formatted with Black
- [ ] Ruff linting passes
- [ ] All tests pass locally
- [ ] New code has tests
- [ ] No sensitive data in commits

## 🔗 Quick Links

- **GitHub Actions**: Check your repo's "Actions" tab
- **Codecov**: https://codecov.io (after setup)
- **Local CI Script**: `./scripts/run_ci_checks.sh`

## 💡 Pro Tips

1. **Run checks before committing** - Save time by catching issues early
2. **Use the local script** - It mimics exactly what CI does
3. **Fix formatting first** - Black and Ruff are quick wins
4. **Don't skip tests** - They catch bugs before production

## 🎓 Learning Resources

- [pytest Tutorial](https://docs.pytest.org/en/stable/getting-started.html)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [GitHub Actions Basics](https://docs.github.com/en/actions/learn-github-actions)

---

**Need Help?** Check `.github/CI_CD_GUIDE.md` for detailed information.
