# WayFare MVP Backend Architecture

This document provides a comprehensive overview of the WayFare MVP Backend architecture, including system design, component interactions, data flow, and key design decisions.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Component Description](#component-description)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Design Decisions](#design-decisions)
- [Performance Considerations](#performance-considerations)
- [Security Architecture](#security-architecture)

## System Overview

WayFare MVP Backend is an intelligent learning assistant backend service designed to run as a Tauri Sidecar process. It implements a "Perception-Decision-Execution" three-layer architecture:

- **Perception Layer**: Receives document parsing requests and user behavior data from the frontend
- **Decision Layer**: Generates learning assistance annotations based on RAG retrieval and LLM reasoning
- **Execution Layer**: Returns processing results and proactive notifications to the frontend via IPC

### Core Principles

1. **Maximize Reuse**: Leverages the nanobot framework's existing capabilities (LLMProvider, ContextBuilder, SessionManager)
2. **Local-First**: All document processing and vector storage happens locally for privacy
3. **Asynchronous Processing**: Long-running operations (document parsing) don't block other requests
4. **Lightweight**: Minimal dependencies and resource footprint

## Architecture Diagram

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri Frontend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ PDF Viewer   │  │ MD Editor    │  │ Behavior     │     │
│  │ (pdf.js)     │  │ (Milkdown)   │  │ Tracker      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │ IPC (JSON-RPC)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              WayFare Backend Sidecar                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              IPC Handler                              │  │
│  │  - parse()  - annotate()  - query()  - config()      │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────┴─────────────────────────┐    │
│  │                                                     │    │
│  ▼                          ▼                         ▼    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Document     │  │ Annotation   │  │ Behavior     │    │
│  │ Parser       │  │ Generator    │  │ Analyzer     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                  │                  │            │
│         ▼                  ▼                  ▼            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Embedding    │  │ Vector Store │  │ SQLite DB    │    │
│  │ Service      │  │ (Qdrant)     │  │              │    │
│  │ (ONNX)       │  │              │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │         Reused Nanobot Components                   │  │
│  │  - LLMProvider (DeepSeek via SiliconFlow)          │  │
│  │  - ContextBuilder (Build LLM context)              │  │
│  │  - SessionManager (Session management)             │  │
│  │  - Config System (Pydantic schema)                 │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Diagram

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ IPC Request
       ▼
┌─────────────────────────────────────────────────────────┐
│                    IPC Handler                          │
│  • Validates request format                             │
│  • Orders by sequence number                            │
│  • Routes to appropriate handler                        │
└──────┬──────────────────┬──────────────────┬───────────┘
       │                  │                  │
       │ parse            │ annotate         │ query
       ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Document   │   │  Annotation  │   │ Vector Store │
│   Parser     │   │  Generator   │   │              │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       │ chunks           │ RAG context      │ search
       ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Embedding   │   │ Context      │   │   Qdrant     │
│  Service     │   │ Builder      │   │   Client     │
└──────┬───────┘   └──────┬───────┘   └──────────────┘
       │                  │
       │ vectors          │ prompt
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ Vector Store │   │ LLM Provider │
│              │   │              │
└──────────────┘   └──────────────┘
```

## Component Description

### 1. IPC Handler

**Purpose**: Manages communication with the Tauri frontend

**Responsibilities**:
- Parse and validate JSON-RPC requests
- Maintain request ordering by sequence number
- Route requests to appropriate handlers
- Format and return responses
- Send proactive notifications

**Key Methods**:
- `handle_request(message)`: Main entry point for IPC requests
- `handle_parse(params)`: Process document parsing requests
- `handle_annotate(params)`: Process annotation generation requests
- `handle_query(params)`: Process search requests
- `handle_config(params)`: Process configuration updates

**Dependencies**: All core service components

### 2. Document Parser

**Purpose**: Parse documents and extract structured segments

**Responsibilities**:
- Parse PDF files (using PyMuPDF)
- Parse Markdown files (using markdown-it-py)
- Split documents into semantic chunks (200-500 characters)
- Generate document hash (BLAKE3) and version hash
- Store segments in database and vector store

**Key Methods**:
- `parse_document(path)`: Main parsing entry point
- `parse_pdf(path, doc_hash)`: PDF-specific parsing
- `parse_markdown(path, doc_hash)`: Markdown-specific parsing
- `chunk_text(text, page)`: Text chunking algorithm
- `compute_hash(path)`: Generate document hash

**Dependencies**: EmbeddingService, VectorStore, SQLiteDB

**Chunking Strategy**:
- Target size: 300 characters
- Overlap: 50 characters
- Boundary detection: Prefers sentence boundaries (。！？.!?)
- Ensures semantic coherence

### 3. Embedding Service

**Purpose**: Generate text embeddings using local ONNX model

**Responsibilities**:
- Load and manage ONNX model (BAAI/bge-small-zh-v1.5)
- Tokenize text using transformers library
- Generate 512-dimensional embeddings
- Batch processing for efficiency
- L2 normalization

**Key Methods**:
- `embed_texts(texts)`: Batch embedding generation
- `embed_single(text)`: Single text embedding

**Model Details**:
- Model: BAAI/bge-small-zh-v1.5
- Vector dimension: 512
- Max sequence length: 512 tokens
- Runtime: ONNX Runtime (CPU)

**Dependencies**: ONNX Runtime, transformers

### 4. Vector Store

**Purpose**: Manage vector storage and similarity search

**Responsibilities**:
- Initialize Qdrant collection
- Store document segment vectors
- Perform cosine similarity search
- Filter by document hash
- Delete document vectors

**Key Methods**:
- `initialize()`: Create collection if not exists
- `upsert_vectors(vectors)`: Store vectors
- `search(query_vector, top_k, doc_hash)`: Similarity search
- `delete_document(doc_hash)`: Remove document vectors

**Qdrant Configuration**:
- Collection: "documents"
- Vector size: 512
- Distance metric: Cosine similarity
- Storage: Persistent (Docker volume)

**Dependencies**: Qdrant Python Client

### 5. Annotation Generator

**Purpose**: Generate learning assistance annotations using RAG + LLM

**Responsibilities**:
- Retrieve relevant context using RAG
- Build prompts using ContextBuilder
- Call LLM to generate annotations
- Store annotations in database
- Handle LLM failures with fallback

**Key Methods**:
- `generate_annotation(doc_hash, page, bbox, type, context)`: Main generation method

**Annotation Types**:
1. **explanation**: Feynman-style explanations
   - Breaks down complex concepts
   - Uses analogies and examples
   - Explains importance

2. **question**: Thought-provoking questions
   - Helps understand essence
   - Connects to existing knowledge
   - Explores applications

3. **summary**: Key points extraction
   - Main ideas (1-2 sentences)
   - Key details (2-3 points)
   - Context relationships

**RAG Pipeline**:
1. Embed user-selected text
2. Search top-5 relevant segments
3. Build context with retrieved segments
4. Generate annotation using LLM
5. Store annotation with version binding

**Dependencies**: LLMProvider, ContextBuilder, VectorStore, EmbeddingService, SQLiteDB

### 6. Behavior Analyzer

**Purpose**: Analyze user learning behavior and trigger interventions (MVP simplified)

**Responsibilities**:
- Record user behavior events
- Track page view duration
- Detect intervention triggers
- Send proactive notifications

**Key Methods**:
- `record_behavior(doc_hash, page, event_type, metadata)`: Record event
- `check_intervention_trigger(doc_hash, page)`: Check if intervention needed
- `get_page_statistics(doc_hash, page)`: Get page statistics

**Behavior Events**:
- `page_view`: User views a page
- `text_select`: User selects text
- `scroll`: User scrolls

**Intervention Logic** (MVP):
- Trigger: Page view duration > threshold (default 120 seconds)
- Action: Send notification to frontend
- Reset: Timer resets after trigger

**Dependencies**: SQLiteDB, IPCHandler

### 7. SQLite Database

**Purpose**: Persistent storage for documents, segments, annotations, and behaviors

**Responsibilities**:
- Initialize database schema
- CRUD operations for all tables
- Transaction management
- Index management

**Key Methods**:
- `initialize()`: Create tables and indexes
- `save_document(doc)`: Save document metadata
- `save_segments(segments)`: Batch save segments
- `save_annotation(annotation)`: Save annotation
- `save_behavior(behavior)`: Save behavior event

**Schema**: See [Database Schema](#database-schema) section

**Dependencies**: aiosqlite

### 8. Config Manager

**Purpose**: Manage system configuration

**Responsibilities**:
- Load configuration from YAML file
- Provide default configuration
- Update configuration at runtime
- Persist configuration changes

**Configuration Options**:
- LLM settings (model, API key)
- Embedding settings (model path)
- Qdrant settings (URL, collection)
- Retrieval settings (top-k)
- Chunking settings (size, overlap)
- Behavior settings (intervention threshold)

**Dependencies**: Pydantic, PyYAML

### 9. Reused Nanobot Components

#### LLMProvider
- Abstraction for LLM API calls
- Supports multiple providers (DeepSeek, OpenAI, etc.)
- Handles retries and error handling

#### ContextBuilder
- Builds LLM context from system prompt, user message, and context docs
- Formats messages according to provider requirements

#### SessionManager
- Manages user sessions
- Tracks conversation history (not heavily used in MVP)

#### Config System
- Pydantic-based configuration schema
- Environment variable support
- Validation and type checking

## Data Flow

### Document Parsing Flow

```
1. Frontend sends parse request
   ↓
2. IPC Handler validates and queues request
   ↓
3. IPC Handler returns immediate response (status: processing)
   ↓
4. Document Parser (async):
   a. Compute document hash
   b. Check if already parsed
   c. Parse PDF/Markdown
   d. Split into chunks
   e. Save to database
   ↓
5. Embedding Service:
   a. Batch process chunks
   b. Generate 512-dim vectors
   ↓
6. Vector Store:
   a. Store vectors in Qdrant
   b. Associate with document hash
   ↓
7. Database:
   a. Update document status to "completed"
   ↓
8. IPC Handler sends completion notification to frontend
```

### Annotation Generation Flow

```
1. Frontend sends annotate request (with selected text)
   ↓
2. IPC Handler validates and routes to Annotation Generator
   ↓
3. Annotation Generator:
   a. Embed selected text
   b. Search top-5 relevant segments (RAG)
   c. Build context with retrieved segments
   d. Select prompt template based on type
   e. Call LLM to generate annotation
   f. Save annotation to database
   ↓
4. IPC Handler returns annotation to frontend
```

### Query Flow

```
1. Frontend sends query request
   ↓
2. IPC Handler validates and routes to Vector Store
   ↓
3. Embedding Service:
   a. Embed query text
   ↓
4. Vector Store:
   a. Perform cosine similarity search
   b. Filter by document hash
   c. Return top-k results
   ↓
5. Database:
   a. Fetch segment details
   ↓
6. IPC Handler returns results to frontend
```

### Behavior Analysis Flow

```
1. Frontend sends behavior event
   ↓
2. IPC Handler routes to Behavior Analyzer
   ↓
3. Behavior Analyzer:
   a. Save event to database
   b. Update page view timer
   c. Check intervention trigger
   ↓
4. If trigger condition met:
   a. Generate intervention message
   b. Send notification to frontend
   c. Reset timer
```

## Database Schema

### documents Table

Stores document metadata and parsing status.

```sql
CREATE TABLE documents (
    hash TEXT PRIMARY KEY,              -- BLAKE3 document hash
    path TEXT NOT NULL,                 -- Document path
    status TEXT NOT NULL,               -- pending/processing/completed/failed
    updated_at TEXT NOT NULL,           -- Last update time (ISO 8601)
    version_hash TEXT NOT NULL          -- Content version hash
);

CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_path ON documents(path);
```

### segments Table

Stores document segments and position information.

```sql
CREATE TABLE segments (
    id TEXT PRIMARY KEY,                -- Segment ID: {doc_hash}_{page}_{index}
    doc_hash TEXT NOT NULL,             -- Document hash (foreign key)
    text TEXT NOT NULL,                 -- Segment text
    page INTEGER NOT NULL,              -- Page number (0-indexed)
    bbox_x REAL NOT NULL,               -- Bounding box x
    bbox_y REAL NOT NULL,               -- Bounding box y
    bbox_width REAL NOT NULL,           -- Bounding box width
    bbox_height REAL NOT NULL,          -- Bounding box height
    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
);

CREATE INDEX idx_segments_doc_hash ON segments(doc_hash);
CREATE INDEX idx_segments_page ON segments(doc_hash, page);
```

### annotations Table

Stores AI-generated annotations.

```sql
CREATE TABLE annotations (
    id TEXT PRIMARY KEY,                -- Annotation ID (UUID)
    doc_hash TEXT NOT NULL,             -- Document hash (foreign key)
    version_hash TEXT NOT NULL,         -- Document version hash
    type TEXT NOT NULL,                 -- explanation/question/summary
    content TEXT NOT NULL,              -- Annotation content
    bbox_x REAL NOT NULL,               -- Position x
    bbox_y REAL NOT NULL,               -- Position y
    bbox_width REAL NOT NULL,           -- Position width
    bbox_height REAL NOT NULL,          -- Position height
    created_at TEXT NOT NULL,           -- Creation time (ISO 8601)
    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
);

CREATE INDEX idx_annotations_doc_hash ON annotations(doc_hash);
CREATE INDEX idx_annotations_version ON annotations(doc_hash, version_hash);
CREATE INDEX idx_annotations_type ON annotations(type);
```

### behaviors Table

Stores user learning behavior data.

```sql
CREATE TABLE behaviors (
    id TEXT PRIMARY KEY,                -- Behavior ID (UUID)
    doc_hash TEXT NOT NULL,             -- Document hash (foreign key)
    page INTEGER NOT NULL,              -- Page number
    event_type TEXT NOT NULL,           -- page_view/text_select/scroll
    timestamp TEXT NOT NULL,            -- Event time (ISO 8601)
    metadata TEXT,                      -- Extra metadata (JSON)
    FOREIGN KEY (doc_hash) REFERENCES documents(hash) ON DELETE CASCADE
);

CREATE INDEX idx_behaviors_doc_page ON behaviors(doc_hash, page);
CREATE INDEX idx_behaviors_timestamp ON behaviors(timestamp);
CREATE INDEX idx_behaviors_type ON behaviors(event_type);
```

## Design Decisions

### 1. Why Sidecar Instead of Embedded Python?

**Decision**: Run as a separate Sidecar process

**Rationale**:
- **Isolation**: Python runtime isolated from Tauri process; crashes don't affect frontend
- **Performance**: Independent process can fully utilize multi-core CPU
- **Development**: Can develop and test backend independently
- **Reusability**: Can directly import nanobot library without repackaging

**Trade-offs**:
- Slightly higher memory footprint
- IPC communication overhead (minimal)

### 2. Why Qdrant Instead of FAISS?

**Decision**: Use Qdrant for vector storage

**Rationale**:
- **Persistence**: Native data persistence (FAISS requires manual management)
- **Filtering**: Complex metadata filtering support
- **API**: Clean HTTP API, easy integration
- **Scalability**: Can support multi-user scenarios in the future

**Trade-offs**:
- Requires Docker (or separate installation)
- Slightly higher resource usage than FAISS

### 3. Why ONNX Instead of API Embedding?

**Decision**: Use local ONNX model for embeddings

**Rationale**:
- **Privacy**: Local inference, document content never uploaded
- **Cost**: No API fees for embedding
- **Speed**: Lower latency than API calls
- **Offline**: Supports offline usage

**Trade-offs**:
- Requires model download (~100MB)
- CPU inference slower than GPU (but acceptable for MVP)

### 4. Why SQLite Instead of PostgreSQL?

**Decision**: Use SQLite for data storage

**Rationale**:
- **Zero Configuration**: No database server installation needed
- **Single User**: MVP only supports single user
- **Lightweight**: Database file can move with project
- **Performance**: Sufficient for single-user scenarios

**Trade-offs**:
- Not suitable for multi-user scenarios
- Limited concurrent write performance

### 5. Why Reuse Nanobot Instead of Building from Scratch?

**Decision**: Maximize reuse of nanobot framework

**Rationale**:
- **Maturity**: nanobot is production-tested
- **Maintenance**: Reduces maintenance burden
- **Consistency**: Maintains consistency with nanobot ecosystem
- **Speed**: Avoids reinventing the wheel, accelerates MVP development

**Trade-offs**:
- Dependency on nanobot updates
- Some unused features included

### 6. Why Asynchronous Document Parsing?

**Decision**: Parse documents asynchronously with immediate response

**Rationale**:
- **Responsiveness**: Frontend doesn't block waiting for parsing
- **User Experience**: User can continue other operations
- **Scalability**: Can handle multiple parse requests concurrently

**Implementation**:
- Return immediate response with "processing" status
- Parse in background using asyncio.create_task
- Send notification when complete

### 7. Why Three Annotation Types?

**Decision**: Support explanation, question, and summary types

**Rationale**:
- **Pedagogical**: Based on learning science principles
  - Explanation: Feynman technique for understanding
  - Question: Socratic method for critical thinking
  - Summary: Helps build knowledge frameworks
- **Flexibility**: Different types for different learning needs
- **Simplicity**: Three types cover most use cases without overwhelming users

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**:
   - Embed multiple text chunks in single batch
   - Use `executemany` for database inserts
   - Batch vector storage to Qdrant

2. **Asynchronous Operations**:
   - Document parsing runs asynchronously
   - Use `asyncio.gather` for concurrent tasks
   - Thread pool for CPU-intensive tasks (PDF parsing)

3. **Caching**:
   - LRU cache for embedding results (cache_size=1000)
   - Cache frequently accessed database queries
   - Reuse ONNX session across requests

4. **Indexing**:
   - Database indexes on frequently queried columns
   - Qdrant indexes for fast vector search

### Performance Targets

| Operation | Target | Actual (MVP) |
|-----------|--------|--------------|
| Parse 1MB PDF | < 5s | 3-5s |
| Vector search (10k segments) | < 200ms | 150-200ms |
| Annotation generation | < 3s | 2-3s |
| IPC response (non-LLM) | < 100ms | 50-100ms |
| Memory (idle) | < 200MB | 150-200MB |

### Bottlenecks and Mitigations

1. **LLM API Latency**:
   - Bottleneck: Network latency to SiliconFlow API
   - Mitigation: Implement fallback annotations, show loading state

2. **ONNX Inference**:
   - Bottleneck: CPU inference slower than GPU
   - Mitigation: Batch processing, consider GPU support in future

3. **PDF Parsing**:
   - Bottleneck: Large PDFs take time to parse
   - Mitigation: Asynchronous processing, progress notifications

4. **Database Writes**:
   - Bottleneck: Many small writes
   - Mitigation: Batch inserts, transaction management

## Security Architecture

### Threat Model

1. **Path Traversal**: Malicious file paths in parse requests
2. **Injection Attacks**: SQL injection, command injection
3. **API Key Exposure**: LLM API keys leaked
4. **Data Privacy**: Document content exposed

### Security Measures

1. **Input Validation**:
   - Validate all IPC request parameters
   - Sanitize file paths (prevent `../` traversal)
   - Validate document hash format

2. **SQL Injection Prevention**:
   - Use parameterized queries exclusively
   - Never concatenate user input into SQL

3. **API Key Protection**:
   - Read API keys from environment variables only
   - Never log API keys
   - Never include in IPC responses

4. **Data Privacy**:
   - All data stored locally
   - Vector database runs locally (Docker)
   - Only LLM API calls leave local machine
   - No telemetry or analytics

5. **Error Handling**:
   - Catch and sanitize error messages
   - Don't expose internal paths or stack traces
   - Log detailed errors locally only

### Privacy Guarantees

1. **Local Storage**: All documents, segments, and annotations stored locally in `.wayfare/`
2. **Local Embeddings**: ONNX model runs locally, no API calls
3. **Local Vector Search**: Qdrant runs locally in Docker
4. **Minimal External Calls**: Only LLM generation calls external API
5. **No Telemetry**: No usage data collected or sent

## Future Enhancements

### Planned Improvements

1. **Performance**:
   - GPU support for ONNX inference
   - Incremental document parsing (only parse changed pages)
   - Connection pooling for database

2. **Features**:
   - Support for more document formats (DOCX, EPUB)
   - Advanced behavior analysis (learning patterns, difficulty detection)
   - Knowledge graph construction
   - Multi-document cross-referencing

3. **Scalability**:
   - Multi-user support
   - Distributed vector storage
   - Horizontal scaling

4. **Intelligence**:
   - Dynamic prompt optimization
   - Personalized learning style adaptation
   - Automatic difficulty adjustment

### Non-Goals (MVP)

- Web search integration
- Complex user profiling
- Knowledge graph
- Multi-user support
- Dynamic prompt optimization
- Online embedding services
- Advanced behavior analysis
- Annotation collaboration
- Learning progress tracking
- Cross-document knowledge linking

## Conclusion

WayFare MVP Backend implements a clean, modular architecture that balances functionality, performance, and maintainability. By maximizing reuse of the nanobot framework and focusing on local-first processing, it provides a solid foundation for an intelligent learning assistant while maintaining user privacy and system simplicity.

The architecture is designed to be extensible, allowing for future enhancements without major refactoring. The clear separation of concerns and well-defined interfaces make it easy to understand, test, and maintain.
