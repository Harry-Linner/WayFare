# WayFare MVP Backend - Build Guide

This guide explains how to package the WayFare MVP Backend as a standalone executable using PyInstaller for deployment as a Tauri sidecar.

## Prerequisites

### 1. Python Environment

Ensure you have Python 3.9 or later installed:

```bash
python --version
```

### 2. Install Dependencies

Install all required dependencies:

```bash
# Install production dependencies
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller
```

### 3. Download ONNX Model

The embedding model is required for the backend to function. Download it before building:

```bash
# Create models directory
mkdir -p wayfare/models

# Download the ONNX model
# Option 1: Using wget
wget https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx \
     -O wayfare/models/bge-small-zh-v1.5.onnx

# Option 2: Using curl
curl -L https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx \
     -o wayfare/models/bge-small-zh-v1.5.onnx

# Option 3: Manual download
# Visit: https://huggingface.co/BAAI/bge-small-zh-v1.5
# Download the ONNX model and place it in wayfare/models/
```

## Building the Executable

### Method 1: Using the Build Script (Recommended)

The build script automates the entire process and performs validation checks:

```bash
# Basic build
python build.py

# Clean build (removes previous build artifacts)
python build.py --clean

# Build and test
python build.py --clean --test
```

### Method 2: Using PyInstaller Directly

If you prefer to use PyInstaller directly:

```bash
# Build using the spec file
pyinstaller build.spec

# The executable will be in dist/wayfare-backend (or wayfare-backend.exe on Windows)
```

## Build Output

After a successful build, you'll find:

```
dist/
└── wayfare-backend          # Standalone executable (or .exe on Windows)
```

The executable includes:
- All Python dependencies
- ONNX runtime
- Qdrant client
- Document parsing libraries
- LLM provider integrations
- Configuration templates

## Testing the Executable

### Basic Test

Test that the executable runs:

```bash
# Check version
./dist/wayfare-backend --version

# Show help
./dist/wayfare-backend --help
```

### Integration Test

Test with a workspace:

```bash
# Create a test workspace
mkdir -p test_workspace

# Run the backend
./dist/wayfare-backend --workspace test_workspace --log-level DEBUG
```

The backend should:
1. Initialize all components
2. Create `.wayfare/` directory in the workspace
3. Start listening on stdin for IPC messages
4. Log initialization steps to `.wayfare/wayfare.log`

Press Ctrl+C to stop.

## Deployment to Tauri

### 1. Copy Executable to Tauri Project

```bash
# Copy to Tauri binaries directory
cp dist/wayfare-backend <your-tauri-project>/src-tauri/binaries/

# On Windows
copy dist\wayfare-backend.exe <your-tauri-project>\src-tauri\binaries\
```

### 2. Configure Tauri

Update `tauri.conf.json` to include the sidecar:

```json
{
  "tauri": {
    "bundle": {
      "externalBin": [
        "binaries/wayfare-backend"
      ]
    },
    "allowlist": {
      "shell": {
        "sidecar": true,
        "scope": [
          {
            "name": "wayfare-backend",
            "sidecar": true,
            "args": true
          }
        ]
      }
    }
  }
}
```

### 3. Start Sidecar from Tauri

In your Tauri Rust code:

```rust
use tauri::api::process::{Command, CommandEvent};

// Start the sidecar
let (mut rx, _child) = Command::new_sidecar("wayfare-backend")?
    .args(&["--workspace", workspace_path])
    .spawn()
    .expect("Failed to spawn wayfare-backend");

// Listen to sidecar output
tauri::async_runtime::spawn(async move {
    while let Some(event) = rx.recv().await {
        match event {
            CommandEvent::Stdout(line) => {
                // Handle IPC response
                println!("Backend: {}", line);
            }
            CommandEvent::Stderr(line) => {
                eprintln!("Backend error: {}", line);
            }
            _ => {}
        }
    }
});
```

## Troubleshooting

### Build Fails with "Module not found"

If PyInstaller can't find a module, add it to `hiddenimports` in `build.spec`:

```python
hiddenimports=[
    # ... existing imports ...
    'your_missing_module',
],
```

### Executable is Too Large

The executable size is typically 200-400 MB due to:
- ONNX runtime (~100 MB)
- Transformers library (~50 MB)
- PyMuPDF (~30 MB)
- Other dependencies

To reduce size:
1. Remove unused dependencies from `requirements.txt`
2. Use UPX compression (already enabled in `build.spec`)
3. Exclude unnecessary packages in the `excludes` list

### Runtime Error: "Model not found"

If the executable can't find the ONNX model:

1. Check that the model was included in the build:
   ```bash
   # On Unix-like systems
   unzip -l dist/wayfare-backend | grep onnx
   
   # On Windows, use 7-Zip or similar
   ```

2. Verify the model path in `config.yaml`:
   ```yaml
   embedding_model_path: "wayfare/models/bge-small-zh-v1.5.onnx"
   ```

3. If the model wasn't included, place it next to the executable and update the config:
   ```yaml
   embedding_model_path: "./bge-small-zh-v1.5.onnx"
   ```

### Runtime Error: "Qdrant connection failed"

Ensure Qdrant is running:

```bash
# Start Qdrant with Docker
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Or update config.yaml to use a different Qdrant URL
```

### Executable Crashes on Startup

Check the logs:

```bash
# Run with debug logging
./dist/wayfare-backend --workspace test_workspace --log-level DEBUG

# Check the log file
cat test_workspace/.wayfare/wayfare.log
```

Common issues:
- Missing dependencies (check `hiddenimports` in `build.spec`)
- Incorrect file paths (use absolute paths or paths relative to workspace)
- Insufficient permissions (ensure write access to workspace directory)

## Platform-Specific Notes

### Windows

- The executable is named `wayfare-backend.exe`
- Antivirus software may flag the executable (add an exception if needed)
- Use PowerShell or Command Prompt to run the executable

### macOS

- The executable may be blocked by Gatekeeper
- Allow it in System Preferences > Security & Privacy
- Or remove the quarantine attribute:
  ```bash
  xattr -d com.apple.quarantine dist/wayfare-backend
  ```

### Linux

- Ensure the executable has execute permissions:
  ```bash
  chmod +x dist/wayfare-backend
  ```
- Some distributions may require additional libraries (check with `ldd`)

## Advanced Configuration

### Custom Build Options

Edit `build.spec` to customize the build:

```python
# Add custom data files
datas=[
    ('path/to/custom/file', 'destination/in/bundle'),
],

# Add more hidden imports
hiddenimports=[
    'your_custom_module',
],

# Change executable name
name='custom-name',

# Add icon (Windows/macOS)
icon='path/to/icon.ico',
```

### Multi-Platform Builds

To build for multiple platforms, you need to build on each platform:

```bash
# On Windows
python build.py --clean

# On macOS
python build.py --clean

# On Linux
python build.py --clean
```

Then collect all executables for distribution.

## Performance Optimization

### Startup Time

The executable may take 2-5 seconds to start due to:
- Python runtime initialization
- Loading ONNX model
- Initializing Qdrant client

This is normal for PyInstaller executables.

### Runtime Performance

Once started, the backend performs the same as running from source:
- Document parsing: ~5 seconds for 1MB PDF
- Embedding generation: ~100ms per text
- Vector search: ~200ms for 10K vectors
- Annotation generation: ~3 seconds (including LLM call)

## Continuous Integration

### GitHub Actions Example

```yaml
name: Build WayFare Backend

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Download ONNX model
        run: |
          mkdir -p wayfare/models
          curl -L https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx \
               -o wayfare/models/bge-small-zh-v1.5.onnx
      
      - name: Build executable
        run: python build.py --clean
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: wayfare-backend-${{ matrix.os }}
          path: dist/wayfare-backend*
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs in `<workspace>/.wayfare/wayfare.log`
3. Open an issue on GitHub with:
   - Your platform (Windows/macOS/Linux)
   - Python version
   - Error messages
   - Relevant log excerpts

## License

See LICENSE file in the project root.
