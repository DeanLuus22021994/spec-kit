# Semantic Kernel Engine

The Engine service is the core processing component that implements Microsoft's Semantic Kernel framework for AI orchestration, enabling natural language understanding and intelligent task execution.

## Overview

- **Technology**: .NET 8.0 with Semantic Kernel SDK
- **Base Image**: .NET 8 Alpine (optimized for size)
- **Port**: Internal service (not directly exposed)
- **Memory**: 1GB (production) for model processing

## Project Structure

```
src/engine/
├── Factories/            # Factory classes for kernel creation
├── kernels/              # Kernel configurations
├── Planners/             # Planner implementations
│   ├── SequentialPlanner
│   ├── ActionPlanner
│   └── StepwisePlanner
├── Plugins/              # Semantic Kernel plugins
├── Skills/               # Semantic skills/functions
├── SemanticKernelService.cs  # Main service implementation
└── engine.csproj         # Project file
```

## Core Components

### SemanticKernelService

The main orchestration service that:

- Manages plugin loading
- Creates execution plans
- Executes kernel requests
- Handles error recovery

```csharp
public class SemanticKernelService
{
    public async Task<KernelResponse> ExecuteAsync(
        KernelRequest request,
        CancellationToken cancellationToken = default);
}
```

### Plugin Manager

Responsible for loading and managing semantic kernel plugins:

```csharp
public interface IPluginManager
{
    Task<IEnumerable<IPlugin>> LoadPluginsAsync(
        CancellationToken cancellationToken = default);
}
```

### Planners

The engine supports multiple planning strategies:

| Planner        | Use Case                | Complexity |
| -------------- | ----------------------- | ---------- |
| **Sequential** | Step-by-step execution  | Low        |
| **Action**     | Single action selection | Low        |
| **Stepwise**   | Complex reasoning       | High       |

## Configuration

### Semantic Kernel Settings

```yaml
semantic_kernel:
  version: "1.0.0"
  plugins_directory: "/app/plugins"
  skills_directory: "/app/skills"
  memory_store: "PostgreSQL"
  vector_dimensions: 1536
  embedding_model: "text-embedding-3-small"
```

### Environment Variables

| Variable                | Description                | Required |
| ----------------------- | -------------------------- | -------- |
| `OPENAI_API_KEY`        | OpenAI API key             | Yes      |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint      | No       |
| `AZURE_OPENAI_KEY`      | Azure OpenAI key           | No       |
| `EMBEDDING_MODEL`       | Embedding model name       | No       |
| `VECTOR_DB_CONNECTION`  | Vector database connection | Yes      |

## Development

### Prerequisites

- .NET 8.0 SDK
- Access to OpenAI or Azure OpenAI
- PostgreSQL with pgvector extension

### Building

```bash
# Build the engine project
dotnet build src/engine/engine.csproj

# Run locally
dotnet run --project src/engine/engine.csproj
```

### Running with Docker

```bash
# Start engine service
docker-compose up engine

# View logs
docker-compose logs -f engine
```

## Creating Plugins

### Plugin Interface

```csharp
public interface IPlugin
{
    string Name { get; }
}
```

### Example Plugin

```csharp
public class SummarizerPlugin : IPlugin
{
    public string Name => "Summarizer";

    [KernelFunction]
    public async Task<string> SummarizeAsync(string text)
    {
        // Implementation
    }
}
```

## Creating Skills

Skills are semantic functions defined in configuration:

```yaml
# skills/summarize/config.yml
name: Summarize
description: Summarizes text content
input:
  - name: text
    description: The text to summarize
prompt: |
  Summarize the following text:
  {{$text}}
```

## Memory and Embeddings

The engine uses pgvector for semantic memory:

```csharp
// Store memory
await memory.SaveInformationAsync(
    collection: "documents",
    text: "Important information",
    id: "doc-1");

// Search memory
var results = await memory.SearchAsync(
    collection: "documents",
    query: "find important info",
    limit: 10);
```

### Vector Configuration

- **Dimensions**: 1536 (OpenAI text-embedding-3-small)
- **Index Type**: IVFFlat for efficient similarity search
- **Distance Metric**: Cosine similarity

## API Reference

### KernelRequest

```csharp
public class KernelRequest
{
    public string Input { get; set; }
}
```

### KernelResponse

```csharp
public class KernelResponse
{
    public bool Success { get; set; }
    public object? Result { get; set; }
    public string? ErrorMessage { get; set; }
}
```

## Error Handling

The engine implements comprehensive error handling:

- **OperationCanceledException**: Graceful cancellation
- **InvalidOperationException**: Configuration/setup errors
- **General exceptions**: Logged and reported

## Resource Limits

| Resource | Production | Development |
| -------- | ---------- | ----------- |
| CPU      | 2.0        | 4.0         |
| Memory   | 1GB        | 2GB         |

Higher resource allocation accounts for:

- Model inference operations
- Embedding generation
- Plan execution

## Testing

```bash
# Run engine unit tests
dotnet test tests/engine-tests/

# Run with coverage
dotnet test tests/engine-tests/ --collect:"XPlat Code Coverage"
```

## Performance Considerations

1. **Caching**: Frequently used embeddings are cached in Redis
2. **Batching**: Embedding requests are batched when possible
3. **Async Operations**: All I/O operations are async
4. **Connection Pooling**: Database connections are pooled

## Monitoring

### Health Metrics

- Plugin load status
- Planner execution times
- Memory store connectivity
- Token usage tracking

### Logging

```csharp
_logger.LogInformation("Starting kernel execution for request");
_logger.LogWarning("Kernel execution was cancelled");
_logger.LogError(ex, "Unexpected error during kernel execution");
```

## Integration Points

The Engine communicates with:

- **Backend API**: Receives processing requests
- **PostgreSQL/pgvector**: Vector storage and retrieval
- **Redis**: Caching layer
- **OpenAI/Azure OpenAI**: LLM and embedding APIs

## Troubleshooting

### Common Issues

1. **Plugin Load Failures**

   - Check plugin directory permissions
   - Verify plugin assembly references

2. **Embedding Errors**

   - Verify API key configuration
   - Check rate limits

3. **Memory Search Returns Empty**

   - Verify vector dimensions match
   - Check collection name spelling

4. **High Memory Usage**
   - Review batch sizes
   - Check for memory leaks in custom plugins

## Related Documentation

- [Architecture Overview](../../ARCHITECTURE.md)
- [Development Guide](../../DEVELOPMENT.md)
- [Backend API](../backend/README.md)
- [Database Schema](../../infrastructure/database/README.md)
