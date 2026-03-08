# WayFare Backend IPC API Documentation

This document describes the IPC (Inter-Process Communication) interface between the Tauri frontend and WayFare backend. The backend listens for JSON-RPC formatted requests on stdin and outputs responses to stdout.

## Protocol Overview

### Request Format

All requests follow this JSON structure:

```json
{
  "id": "unique-request-id",
  "seq": 1,
  "method": "method_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Fields**:
- `id` (string, required): Unique identifier for the request (typically UUID)
- `seq` (integer, required): Sequence number for request ordering (prevents "先发后到" issues)
- `method` (string, required): Method name to invoke (`parse`, `annotate`, `query`, `config`)
- `params` (object, required): Method-specific parameters

### Response Format

All responses follow this JSON structure:

```json
{
  "id": "unique-request-id",
  "seq": 1,
  "success": true,
  "data": {
    "result1": "value1",
    "result2": "value2"
  }
}
```

**Success Response Fields**:
- `id` (string): Matches the request ID
- `seq` (integer): Matches the request sequence number
- `success` (boolean): `true` for successful operations
- `data` (object): Method-specific response data

**Error Response Fields**:
```json
{
  "id": "unique-request-id",
  "seq": 1,
  "success": false,
  "error": "Error description"
}
```

- `success` (boolean): `false` for failed operations
- `error` (string): Human-readable error message

## Methods

### 1. parse

Parse a document (PDF or Markdown) and generate embeddings for semantic search.

**Request**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "seq": 1,
  "method": "parse",
  "params": {
    "path": "/path/to/document.pdf"
  }
}
```

**Parameters**:
- `path` (string, required): Absolute or relative path to the document file

**Response** (immediate):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "seq": 1,
  "success": true,
  "data": {
    "docHash": "blake3_hash_of_file",
    "status": "processing"
  }
}
```

**Response Fields**:
- `docHash` (string): BLAKE3 hash of the document (unique identifier)
- `status` (string): `"processing"` - parsing is happening asynchronously

**Completion Notification** (pushed via stdout when parsing completes):
```json
{
  "type": "notification",
  "data": {
    "type": "parse_completed",
    "docHash": "blake3_hash_of_file",
    "segmentCount": 42,
    "status": "completed"
  }
}
```

**Failure Notification** (if parsing fails):
```json
{
  "type": "notification",
  "data": {
    "type": "parse_failed",
    "docHash": "blake3_hash_of_file",
    "error": "Error description",
    "status": "failed"
  }
}
```

**Example**:
```bash
# Request
echo '{"id":"1","seq":1,"method":"parse","params":{"path":"./docs/intro.pdf"}}' | python -m wayfare.main

# Immediate response
{"id":"1","seq":1,"success":true,"data":{"docHash":"abc123...","status":"processing"}}

# Later notification (when complete)
{"type":"notification","data":{"type":"parse_completed","docHash":"abc123...","segmentCount":25,"status":"completed"}}
```

**Notes**:
- Parsing is asynchronous and may take several seconds for large documents
- The document is split into 200-500 character chunks
- Each chunk is embedded using the local ONNX model
- Embeddings are stored in Qdrant for semantic search

---

### 2. annotate

Generate an AI annotation for selected text in a document.

**Request**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "seq": 2,
  "method": "annotate",
  "params": {
    "docHash": "blake3_hash_of_file",
    "page": 5,
    "bbox": {
      "x": 100.0,
      "y": 200.0,
      "width": 300.0,
      "height": 50.0
    },
    "type": "explanation",
    "context": "费曼技巧是一种学习方法..."
  }
}
```

**Parameters**:
- `docHash` (string, required): Document hash from parse response
- `page` (integer, required): Page number (0-indexed)
- `bbox` (object, required): Bounding box of the selected text
  - `x` (number): X coordinate
  - `y` (number): Y coordinate
  - `width` (number): Width
  - `height` (number): Height
- `type` (string, required): Annotation type - one of:
  - `"explanation"`: Feynman-style explanation
  - `"question"`: Thought-provoking questions
  - `"summary"`: Key points summary
- `context` (string, required): The selected text to annotate

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "seq": 2,
  "success": true,
  "data": {
    "annotationId": "uuid-of-annotation",
    "content": "费曼技巧的核心是用简单的语言解释复杂概念...",
    "type": "explanation"
  }
}
```

**Response Fields**:
- `annotationId` (string): UUID of the created annotation
- `content` (string): Generated annotation text
- `type` (string): Annotation type (echoed from request)

**Example**:
```bash
echo '{"id":"2","seq":2,"method":"annotate","params":{"docHash":"abc123","page":0,"bbox":{"x":0,"y":0,"width":100,"height":20},"type":"explanation","context":"Machine learning is..."}}' | python -m wayfare.main
```

**Annotation Types**:

1. **explanation**: Uses Feynman technique to explain concepts
   - Breaks down complex ideas into simple language
   - Uses analogies and examples
   - Explains why the concept matters

2. **question**: Generates thought-provoking questions
   - Helps understand the essence of concepts
   - Connects to existing knowledge
   - Explores application scenarios

3. **summary**: Extracts key points
   - Main ideas (1-2 sentences)
   - Key details (2-3 points)
   - Relationship to context

**Notes**:
- Uses RAG (Retrieval-Augmented Generation) to find relevant context
- Retrieves top-5 most relevant document segments
- Calls LLM (DeepSeek via SiliconFlow) to generate annotation
- Annotation is stored in database and bound to document version
- If LLM fails, returns a fallback annotation

---

### 3. query

Search for relevant document segments using semantic search.

**Request**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "seq": 3,
  "method": "query",
  "params": {
    "docHash": "blake3_hash_of_file",
    "query": "什么是费曼技巧？",
    "topK": 5
  }
}
```

**Parameters**:
- `docHash` (string, required): Document hash to search within
- `query` (string, required): Search query text
- `topK` (integer, optional): Number of results to return (default: 5)

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "seq": 3,
  "success": true,
  "data": {
    "results": [
      {
        "segmentId": "abc123_0_1",
        "text": "费曼技巧是一种学习方法，通过用简单的语言解释复杂概念...",
        "page": 0,
        "score": 0.85
      },
      {
        "segmentId": "abc123_1_3",
        "text": "这种方法由物理学家理查德·费曼提出...",
        "page": 1,
        "score": 0.78
      }
    ]
  }
}
```

**Response Fields**:
- `results` (array): Array of search results, sorted by relevance (highest score first)
  - `segmentId` (string): Unique identifier of the segment
  - `text` (string): Segment text content
  - `page` (integer): Page number where segment appears
  - `score` (number): Relevance score (0.0 to 1.0, higher is more relevant)

**Example**:
```bash
echo '{"id":"3","seq":3,"method":"query","params":{"docHash":"abc123","query":"learning methods","topK":3}}' | python -m wayfare.main
```

**Notes**:
- Query text is embedded using the same ONNX model as documents
- Performs cosine similarity search in Qdrant
- Results are filtered to the specified document
- Typical response time: < 200ms for 10,000 segments

---

### 4. config

Update system configuration at runtime.

**Request**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "seq": 4,
  "method": "config",
  "params": {
    "llmModel": "deepseek-chat",
    "embeddingModel": "bge-small-zh-v1.5",
    "retrievalTopK": 5,
    "interventionThreshold": 120
  }
}
```

**Parameters** (all optional):
- `llmModel` (string): LLM model name
- `embeddingModel` (string): Embedding model name
- `retrievalTopK` (integer): Default number of retrieval results
- `interventionThreshold` (integer): Behavior intervention threshold in seconds
- `chunkSize` (integer): Document chunk size in characters
- `chunkOverlap` (integer): Chunk overlap size in characters

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "seq": 4,
  "success": true,
  "data": {
    "updated": true
  }
}
```

**Response Fields**:
- `updated` (boolean): `true` if configuration was updated successfully

**Example**:
```bash
echo '{"id":"4","seq":4,"method":"config","params":{"retrievalTopK":10}}' | python -m wayfare.main
```

**Notes**:
- Configuration changes are persisted to `.wayfare/config.yaml`
- Some changes (like model paths) may require restart to take effect
- Invalid configuration values will return an error response

---

## Error Handling

### Error Response Format

```json
{
  "id": "request-id",
  "seq": 1,
  "success": false,
  "error": "Detailed error message"
}
```

### Common Error Types

**Invalid Request Format**:
```json
{
  "id": "1",
  "seq": 1,
  "success": false,
  "error": "Missing required field: method"
}
```

**Unknown Method**:
```json
{
  "id": "1",
  "seq": 1,
  "success": false,
  "error": "Unknown method: invalid_method"
}
```

**Document Not Found**:
```json
{
  "id": "1",
  "seq": 1,
  "success": false,
  "error": "Document not found: abc123"
}
```

**Parse Error**:
```json
{
  "id": "1",
  "seq": 1,
  "success": false,
  "error": "Failed to parse document: Unsupported file type: .docx"
}
```

**LLM Error**:
```json
{
  "id": "1",
  "seq": 1,
  "success": false,
  "error": "LLM generation failed: API rate limit exceeded"
}
```

## Request Ordering

The backend processes requests in sequence number (`seq`) order to prevent race conditions:

```json
// Request 1 (seq: 1) - arrives first
{"id":"1","seq":1,"method":"parse","params":{"path":"doc.pdf"}}

// Request 2 (seq: 3) - arrives second but has higher seq
{"id":"2","seq":3,"method":"query","params":{"docHash":"abc","query":"test"}}

// Request 3 (seq: 2) - arrives third but has lower seq than request 2
{"id":"3","seq":2,"method":"annotate","params":{...}}
```

Processing order: Request 1 → Request 3 → Request 2

## Notifications

The backend can send proactive notifications via stdout:

### Parse Completion
```json
{
  "type": "notification",
  "data": {
    "type": "parse_completed",
    "docHash": "abc123",
    "segmentCount": 42,
    "status": "completed"
  }
}
```

### Behavior Intervention
```json
{
  "type": "notification",
  "data": {
    "type": "intervention",
    "docHash": "abc123",
    "page": 5,
    "message": "You've been on this page for 2 minutes. Need help understanding?"
  }
}
```

## Performance Characteristics

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| parse (1MB PDF) | 3-5 seconds | Includes embedding generation |
| annotate | 2-3 seconds | Includes LLM call |
| query | < 200ms | For 10,000 segments |
| config | < 50ms | Immediate |

## Example Integration

### Python Client

```python
import json
import subprocess
import sys

class WayFareClient:
    def __init__(self):
        self.process = subprocess.Popen(
            ["python", "-m", "wayfare.main"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.seq = 0
    
    def send_request(self, method, params):
        self.seq += 1
        request = {
            "id": f"req-{self.seq}",
            "seq": self.seq,
            "method": method,
            "params": params
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        return json.loads(response_line)
    
    def parse(self, path):
        return self.send_request("parse", {"path": path})
    
    def annotate(self, doc_hash, page, bbox, type, context):
        return self.send_request("annotate", {
            "docHash": doc_hash,
            "page": page,
            "bbox": bbox,
            "type": type,
            "context": context
        })
    
    def query(self, doc_hash, query, top_k=5):
        return self.send_request("query", {
            "docHash": doc_hash,
            "query": query,
            "topK": top_k
        })

# Usage
client = WayFareClient()

# Parse document
response = client.parse("./docs/intro.pdf")
print(f"Document hash: {response['data']['docHash']}")

# Query
results = client.query(
    doc_hash=response['data']['docHash'],
    query="What is machine learning?"
)
print(f"Found {len(results['data']['results'])} results")

# Annotate
annotation = client.annotate(
    doc_hash=response['data']['docHash'],
    page=0,
    bbox={"x": 0, "y": 0, "width": 100, "height": 20},
    type="explanation",
    context="Machine learning is..."
)
print(f"Annotation: {annotation['data']['content']}")
```

### JavaScript/TypeScript Client (Tauri)

```typescript
import { Command } from '@tauri-apps/api/shell';

class WayFareClient {
  private seq = 0;
  private sidecar: Command;

  constructor() {
    this.sidecar = Command.sidecar('wayfare-backend');
  }

  async sendRequest(method: string, params: any): Promise<any> {
    this.seq++;
    const request = {
      id: `req-${this.seq}`,
      seq: this.seq,
      method,
      params
    };

    const response = await this.sidecar.execute([
      JSON.stringify(request)
    ]);

    return JSON.parse(response.stdout);
  }

  async parse(path: string) {
    return this.sendRequest('parse', { path });
  }

  async annotate(
    docHash: string,
    page: number,
    bbox: { x: number; y: number; width: number; height: number },
    type: 'explanation' | 'question' | 'summary',
    context: string
  ) {
    return this.sendRequest('annotate', {
      docHash,
      page,
      bbox,
      type,
      context
    });
  }

  async query(docHash: string, query: string, topK = 5) {
    return this.sendRequest('query', { docHash, query, topK });
  }
}

// Usage
const client = new WayFareClient();

// Parse document
const parseResponse = await client.parse('./docs/intro.pdf');
console.log('Document hash:', parseResponse.data.docHash);

// Query
const queryResponse = await client.query(
  parseResponse.data.docHash,
  'What is machine learning?'
);
console.log('Results:', queryResponse.data.results);
```

## Security Considerations

1. **Path Validation**: The backend validates file paths to prevent directory traversal attacks
2. **Input Sanitization**: All user inputs are sanitized before processing
3. **API Key Protection**: LLM API keys are read from environment variables, never from requests
4. **Local Processing**: Document content never leaves the local machine (except LLM API calls)
5. **Rate Limiting**: Consider implementing rate limiting in production deployments

## Troubleshooting

### Request Not Processed

**Symptom**: No response received
**Possible Causes**:
- Backend process not running
- Invalid JSON format
- Missing required fields

**Solution**: Check backend logs in `.wayfare/wayfare.log`

### Parse Fails

**Symptom**: `parse_failed` notification
**Possible Causes**:
- Unsupported file format
- Corrupted file
- Insufficient permissions

**Solution**: Verify file exists and is readable

### Annotation Generation Slow

**Symptom**: annotate takes > 5 seconds
**Possible Causes**:
- LLM API rate limiting
- Network latency
- Large document with many segments

**Solution**: Check API key and network connection

### Query Returns No Results

**Symptom**: Empty results array
**Possible Causes**:
- Document not parsed yet
- Query too specific
- Wrong docHash

**Solution**: Ensure document is parsed (status: completed) before querying
