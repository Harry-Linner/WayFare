# WayFare MVP Backend - Main Program

## Overview

`wayfare/main.py` is the main entry point for the WayFare MVP Backend. It runs as a Tauri sidecar process and communicates with the frontend via stdin/stdout using JSON-RPC protocol.

## Features

- **Command-line argument parsing**: `--workspace`, `--config`, `--log-level`
- **Component initialization**: Initializes all components in the correct dependency order
- **IPC server**: Listens on stdin, writes to stdout
- **Graceful shutdown**: Handles SIGINT and SIGTERM signals
- **Error handling**: Comprehensive error handling with user-friendly messages
- **Logging**: File and console logging with automatic rotation

## Usage

### Basic Usage

```bash
python -m wayfare.main --workspace /path/to/workspace
```

### With Custom Config

```bash
python -m wayfare.main --workspace /path/to/workspace --config config.yaml
```

### With Debug Logging

```bash
python -m wayfare.main --workspace /path/to/workspace --log-level DEBUG
```

### Show Help

```bash
python -m wayfare.main --help
```

## Command-Line Arguments

### Required Arguments

- `--workspace PATH`: Workspace directory path (required)
  - This is where the `.wayfare` directory will be created
  - Contains the database, logs, and configuration files

### Optional Arguments

- `--config PATH`: Configuration file path
  - Default: `<workspace>/.wayfare/config.yaml`
  - If not exists, a default config will be created

- `--log-level LEVEL`: Log level
  - Choices: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Default: `INFO`
  - File logs use this level, console logs use WARNING

- `--version`: Show version and exit

## Environment Variables

The following environment variables can override configuration values:

- `WAYFARE_*`: Override any configuration value
  - Example: `WAYFARE_LLM_MODEL=deepseek-chat`
  - Example: `WAYFARE_CHUNK_SIZE=400`

- `SILICONFLOW_API_KEY`: SiliconFlow API key for LLM access
  - Required for annotation generation
  - Can also be set in config file

## Component Initialization Order

The main program initializes components in the following order:

1. **Logging System**: Setup file and console logging
2. **Configuration Manager**: Load config from file or create default
3. **Error Monitor**: Initialize error tracking
4. **SQLite Database**: Create tables and indexes
5. **Qdrant Vector Store**: Connect and create collection
6. **ONNX Embedding Model**: Load bge-small-zh-v1.5 model
7. **LLM Provider**: Initialize SiliconFlow + DeepSeek
8. **Context Builder**: Setup prompt templates
9. **Document Parser**: Initialize with dependencies
10. **Annotation Generator**: Initialize with dependencies
11. **Behavior Analyzer**: Initialize with database
12. **IPC Handler**: Initialize with all dependencies

## IPC Protocol

The main program communicates with the Tauri frontend using JSON-RPC over stdin/stdout:

### Request Format

```json
{
  "id": "uuid",
  "seq": 1,
  "method": "parse",
  "params": {
    "path": "/path/to/document.pdf"
  }
}
```

### Response Format

```json
{
  "id": "uuid",
  "seq": 1,
  "success": true,
  "data": {
    "docHash": "blake3_hash",
    "status": "processing"
  }
}
```

### Supported Methods

- `parse`: Parse a document (PDF or Markdown)
- `annotate`: Generate an annotation
- `query`: Search for relevant segments
- `config`: Update configuration
- `behavior`: Record user behavior

## Graceful Shutdown

The main program handles shutdown signals gracefully:

1. **SIGINT** (Ctrl+C): Graceful shutdown
2. **SIGTERM**: Graceful shutdown
3. **EOF on stdin**: Tauri process terminated

During shutdown:
- Stop IPC handler background tasks
- Close database connections
- Flush and close log files

## Logging

### Log Files

Logs are stored in `<workspace>/.wayfare/wayfare.log`:

- **File logging**: INFO level and above
- **Console logging**: WARNING level and above (to stderr)
- **Automatic rotation**: 10MB per file, 5 backups

### Log Format

```
2024-01-01 12:00:00,000 - wayfare - INFO - Message
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General informational messages
- `WARNING`: Warning messages (potential issues)
- `ERROR`: Error messages (recoverable errors)
- `CRITICAL`: Critical errors (unrecoverable)

## Error Handling

### Recoverable Errors

These errors are logged but don't stop the server:

- `DocumentParseError`: Document parsing failed
- `VectorSearchError`: Vector search failed
- `LLMGenerationError`: LLM generation failed (uses fallback)
- `DatabaseError`: Database operation failed
- `ValidationError`: Input validation failed

### Unrecoverable Errors

These errors cause the program to exit:

- `ModelLoadError`: ONNX model loading failed
- `DatabaseInitError`: Database initialization failed
- `ConfigurationError`: Configuration error

## Directory Structure

After running, the workspace will have the following structure:

```
workspace/
├── .wayfare/
│   ├── config.yaml          # Configuration file
│   ├── wayfare.db           # SQLite database
│   ├── wayfare.log          # Current log file
│   ├── wayfare.log.1        # Rotated log file
│   └── ...
└── your_documents/
    ├── document1.pdf
    └── document2.md
```

## Running as Tauri Sidecar

In your Tauri configuration (`tauri.conf.json`):

```json
{
  "tauri": {
    "bundle": {
      "externalBin": [
        "wayfare-backend"
      ]
    }
  }
}
```

The Tauri frontend will:
1. Start the backend process
2. Communicate via stdin/stdout
3. Terminate the process on exit

## Troubleshooting

### Model Not Found

```
Error: Embedding model not found: ./models/bge-small-zh-v1.5.onnx
```

**Solution**: Download the model from HuggingFace:
```bash
# Download model (example)
wget https://huggingface.co/BAAI/bge-small-zh-v1.5/resolve/main/onnx/model.onnx -O models/bge-small-zh-v1.5.onnx
```

### Qdrant Connection Failed

```
Error: Failed to connect to Qdrant at http://localhost:6333
```

**Solution**: Start Qdrant server:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

### API Key Not Found

```
Warning: SiliconFlow API key not found
```

**Solution**: Set the environment variable:
```bash
export SILICONFLOW_API_KEY=your_api_key
```

Or add to config file:
```yaml
llm_api_key: your_api_key
```

## Development

### Running Locally

```bash
# Create a test workspace
mkdir -p test_workspace

# Run the backend
python -m wayfare.main --workspace test_workspace --log-level DEBUG
```

### Testing IPC

Send JSON requests via stdin:

```bash
echo '{"id":"test1","seq":1,"method":"parse","params":{"path":"test.pdf"}}' | python -m wayfare.main --workspace test_workspace
```

### Debugging

Enable debug logging to see detailed information:

```bash
python -m wayfare.main --workspace test_workspace --log-level DEBUG
```

Check the log file:

```bash
tail -f test_workspace/.wayfare/wayfare.log
```

## Performance

### Startup Time

- Cold start: ~2-5 seconds (loading ONNX model)
- Warm start: ~1-2 seconds (model cached)

### Memory Usage

- Idle: ~200MB
- Processing document: ~300-500MB
- Peak (large document): ~800MB

### Response Times

- Parse request: Immediate (async processing)
- Annotate request: 2-5 seconds (including LLM call)
- Query request: 100-300ms (vector search)
- Config request: <10ms

## Requirements

### Python Version

- Python 3.10 or higher

### Dependencies

See `requirements.txt` for full list:

- `aiosqlite`: Async SQLite
- `qdrant-client`: Vector database client
- `onnxruntime`: ONNX model inference
- `transformers`: Tokenizer
- `PyMuPDF`: PDF parsing
- `markdown-it-py`: Markdown parsing
- `blake3`: Fast hashing
- `pydantic`: Data validation
- `pyyaml`: YAML parsing
- `nanobot`: LLM provider framework

## License

MIT License

## Support

For issues and questions, please refer to the main project documentation.
