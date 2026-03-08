# WayFare MVP Backend - Setup Guide

This guide explains how to set up the WayFare MVP Backend development environment using the automated setup scripts.

## Prerequisites

### All Platforms
- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Docker** (optional but recommended) - [Download Docker](https://www.docker.com/products/docker-desktop)
  - Required for running Qdrant vector database
  - If Docker is not available, you'll need to manually set up Qdrant

### Platform-Specific Requirements

#### Linux/Mac
- `bash` shell (usually pre-installed)
- `curl` or `wget` (for downloading ONNX model)

#### Windows
- PowerShell or Command Prompt
- `curl` (included in Windows 10+) or PowerShell for downloads

## Quick Start

### Linux/Mac

```bash
# Make the script executable (if needed)
chmod +x setup.sh

# Run the setup script
./setup.sh
```

### Windows

```cmd
# Run the setup script
setup.bat
```

## What the Setup Scripts Do

The setup scripts automate the following tasks:

1. **Check Prerequisites**
   - Verify Python 3 installation
   - Check if Docker is available

2. **Create Virtual Environment**
   - Create a Python virtual environment in `./venv`
   - Skip if virtual environment already exists

3. **Install Dependencies**
   - Upgrade pip to the latest version
   - Install all dependencies from `requirements-dev.txt`
   - Includes production dependencies, testing frameworks, and development tools

4. **Setup Models Directory**
   - Create `wayfare/models/` directory if it doesn't exist

5. **Download ONNX Model**
   - Download BAAI/bge-small-zh-v1.5 ONNX model (~100MB)
   - Save to `wayfare/models/bge-small-zh-v1.5.onnx`
   - Skip if model already exists

6. **Start Qdrant Container**
   - Create and start a Docker container named `wayfare-qdrant`
   - Expose Qdrant on port 6333
   - Mount persistent storage at `.wayfare/qdrant_storage`
   - Skip if Docker is not available

7. **Verify Installation**
   - Run `verify_dependencies.py` to check all dependencies
   - Report any missing or incompatible packages

## After Setup

### Activate Virtual Environment

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate.bat
```

### Set API Key (Optional)

If you plan to use LLM features with SiliconFlow/OpenAI:

**Linux/Mac:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Windows:**
```cmd
set OPENAI_API_KEY=your-api-key-here
```

### Run Tests

```bash
pytest tests/
```

### Start the Backend

```bash
python wayfare/main.py
```

## Managing Qdrant

If Docker is available, the setup script creates a Qdrant container. You can manage it using:

### Stop Qdrant
```bash
docker stop wayfare-qdrant
```

### Start Qdrant
```bash
docker start wayfare-qdrant
```

### View Qdrant Logs
```bash
docker logs wayfare-qdrant
```

### Remove Qdrant Container
```bash
docker stop wayfare-qdrant
docker rm wayfare-qdrant
```

### Access Qdrant Web UI
Open your browser and navigate to:
```
http://localhost:6333/dashboard
```

## Manual Qdrant Setup (Without Docker)

If Docker is not available, you can:

1. **Download Qdrant Binary**
   - Visit [Qdrant Releases](https://github.com/qdrant/qdrant/releases)
   - Download the appropriate binary for your platform

2. **Run Qdrant**
   ```bash
   ./qdrant
   ```

3. **Or Use Qdrant Cloud**
   - Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
   - Update `config.yaml` with your cloud instance URL

## Troubleshooting

### Python Not Found

**Issue:** Script reports "Python is not installed"

**Solution:**
- Install Python 3.8+ from [python.org](https://www.python.org/)
- Ensure Python is added to your system PATH
- On Linux/Mac, you may need to use `python3` instead of `python`

### Docker Not Available

**Issue:** Script reports "Docker is not installed"

**Solution:**
- Install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
- Or follow the manual Qdrant setup instructions above
- The script will continue without Docker, but you'll need to set up Qdrant manually

### ONNX Model Download Fails

**Issue:** Model download fails or times out

**Solution:**
- Check your internet connection
- Manually download the model from:
  ```
  https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx
  ```
- Save it to `wayfare/models/bge-small-zh-v1.5.onnx`

### Qdrant Container Fails to Start

**Issue:** Docker container creation fails

**Solution:**
- Check if port 6333 is already in use:
  ```bash
  # Linux/Mac
  lsof -i :6333
  
  # Windows
  netstat -ano | findstr :6333
  ```
- Stop any process using port 6333
- Or modify the port in the setup script

### Dependencies Installation Fails

**Issue:** pip install fails with errors

**Solution:**
- Ensure you have the latest pip:
  ```bash
  python -m pip install --upgrade pip
  ```
- Check if you have sufficient disk space
- On Linux, you may need to install system dependencies:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-dev build-essential
  
  # CentOS/RHEL
  sudo yum install python3-devel gcc
  ```

### Virtual Environment Activation Fails

**Issue:** Cannot activate virtual environment

**Solution:**
- **Windows PowerShell:** You may need to enable script execution:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **Linux/Mac:** Ensure the script has execute permissions:
  ```bash
  chmod +x venv/bin/activate
  ```

## Re-running Setup

The setup scripts are **idempotent**, meaning they can be safely run multiple times:

- Existing virtual environment will be reused
- Existing ONNX model will not be re-downloaded
- Existing Qdrant container will be reused or started if stopped

To force a fresh setup:

1. **Remove virtual environment:**
   ```bash
   rm -rf venv  # Linux/Mac
   rmdir /s venv  # Windows
   ```

2. **Remove ONNX model:**
   ```bash
   rm wayfare/models/bge-small-zh-v1.5.onnx  # Linux/Mac
   del wayfare\models\bge-small-zh-v1.5.onnx  # Windows
   ```

3. **Remove Qdrant container:**
   ```bash
   docker stop wayfare-qdrant
   docker rm wayfare-qdrant
   ```

4. **Run setup script again**

## Configuration

After setup, you can customize the configuration in `config.yaml`:

- **Qdrant address:** Change `db.qdrant.addr` if using a different host/port
- **ONNX model path:** Change `embedding.onnx_path` if you moved the model
- **LLM provider:** Configure `llm.openai.base_url` and `llm.openai.model`
- **Logging:** Adjust `logging.level` and `logging.file`

## Next Steps

After successful setup:

1. **Read the documentation:**
   - `README.md` - Project overview
   - `BUILD.md` - Build and deployment guide
   - `DEPENDENCIES.md` - Dependency details

2. **Explore examples:**
   - Check the `examples/` directory for usage examples

3. **Run tests:**
   - `pytest tests/` - Run all tests
   - `pytest tests/wayfare/` - Run WayFare-specific tests

4. **Start developing:**
   - Activate the virtual environment
   - Make your changes
   - Run tests to verify
   - Submit a pull request

## Support

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/your-repo/wayfare/issues)
2. Review the project documentation
3. Ask for help in the project's communication channels

## License

This project is licensed under the terms specified in the LICENSE file.
