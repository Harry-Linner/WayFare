# WayFare Backend - Quick Build Guide

## TL;DR

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Download ONNX model (optional, ~100MB)
mkdir -p wayfare/models
wget https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx \
     -O wayfare/models/bge-small-zh-v1.5.onnx

# 3. Build
python build.py --clean --test

# 4. Test
./dist/wayfare-backend --version

# 5. Deploy to Tauri
cp dist/wayfare-backend <tauri-project>/src-tauri/binaries/
```

## What Gets Built

- **Input**: Python source code + dependencies
- **Output**: Single executable file (~200-400 MB)
- **Platform**: Build on target platform (Windows/macOS/Linux)
- **Location**: `dist/wayfare-backend` (or `.exe` on Windows)

## What's Included

✓ All Python dependencies  
✓ ONNX runtime  
✓ Qdrant client  
✓ Document parsing libraries  
✓ LLM provider integrations  
✓ Configuration templates  
✓ ONNX model (if present in wayfare/models/)  

## What's NOT Included

✗ Qdrant server (must run separately)  
✗ Development tools (pytest, hypothesis)  
✗ Source code (compiled to bytecode)  

## Build Options

```bash
# Basic build
python build.py

# Clean build (recommended)
python build.py --clean

# Build and test
python build.py --clean --test

# Direct PyInstaller (advanced)
pyinstaller build.spec
```

## Validation Before Building

```bash
# Check configuration
python test_build_config.py

# Should show:
# ✓ PASS: Spec file
# ✓ PASS: Entry point
# ✓ PASS: Data files
# ✓ PASS: Hidden imports
# ✓ PASS: WayFare imports
```

## Common Issues

### "PyInstaller not found"
```bash
pip install pyinstaller
```

### "Module not found" during build
Add to `hiddenimports` in `build.spec`:
```python
hiddenimports=[
    # ... existing imports ...
    'your_missing_module',
],
```

### "Model not found" at runtime
Either:
1. Place model in `wayfare/models/` before building, OR
2. Place model next to executable after building

### Executable too large
Normal size is 200-400 MB due to:
- ONNX runtime (~100 MB)
- Transformers (~50 MB)
- PyMuPDF (~30 MB)
- Other dependencies (~50-100 MB)

## Platform-Specific Notes

### Windows
- Output: `wayfare-backend.exe`
- May need antivirus exception
- Use PowerShell or CMD

### macOS
- Output: `wayfare-backend`
- May need Gatekeeper approval
- Remove quarantine: `xattr -d com.apple.quarantine dist/wayfare-backend`

### Linux
- Output: `wayfare-backend`
- Set executable: `chmod +x dist/wayfare-backend`
- May need additional libraries

## Testing the Build

```bash
# Version check
./dist/wayfare-backend --version

# Help text
./dist/wayfare-backend --help

# Full test with workspace
mkdir test_workspace
./dist/wayfare-backend --workspace test_workspace --log-level DEBUG
# Press Ctrl+C to stop
```

## Deployment Checklist

- [ ] Build executable on target platform
- [ ] Test executable with `--version`
- [ ] Copy to Tauri project: `src-tauri/binaries/`
- [ ] Update `tauri.conf.json` with sidecar config
- [ ] Test Tauri integration
- [ ] Ensure Qdrant is running
- [ ] Verify IPC communication

## Need More Details?

See `BUILD.md` for comprehensive documentation including:
- Detailed troubleshooting
- Tauri integration examples
- CI/CD setup
- Performance optimization
- Advanced configuration

## Support

If you encounter issues:
1. Check `BUILD.md` troubleshooting section
2. Run `python test_build_config.py` to validate setup
3. Check logs in `<workspace>/.wayfare/wayfare.log`
4. Open GitHub issue with error details
