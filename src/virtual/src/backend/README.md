# Backend API Service

The Backend API is an ASP.NET Core Web API service that provides the primary REST API interface for the Semantic Kernel Application.

## Overview

- **Technology**: ASP.NET Core 8.0
- **Base Image**: .NET 8 Alpine (optimized for size)
- **Port**: 5000 (internal), 80 (container)
- **Health Check**: `/health`

## Project Structure

```
src/backend/
├── Controllers/          # API endpoints
├── Models/              # Data transfer objects
├── Services/            # Business logic services
├── Program.cs           # Application entry point
├── appsettings.json     # Configuration
└── backend.csproj       # Project file
```

## API Endpoints

### Health Check

```http
GET /health
```

Returns the health status of the API.

### Swagger Documentation

When running in development mode, Swagger UI is available at:

```
http://localhost:5000/swagger
```

## Configuration

The API uses the following configuration hierarchy:

1. `appsettings.json` - Base configuration
2. `appsettings.{Environment}.json` - Environment-specific overrides
3. Environment variables - Runtime overrides

### Key Settings

| Setting                      | Description       | Default       |
| ---------------------------- | ----------------- | ------------- |
| `Kestrel:Endpoints:Http:Url` | API listening URL | `http://+:80` |
| `Logging:LogLevel:Default`   | Default log level | `Information` |

## Development

### Prerequisites

- .NET 8.0 SDK
- Docker (for containerized development)

### Building

```bash
# Build the project
dotnet build src/backend/backend.csproj

# Run locally
dotnet run --project src/backend/backend.csproj
```

### Running in Docker

```bash
# Build and run with Docker Compose
docker-compose up backend

# View logs
docker-compose logs -f backend
```

## Testing

```bash
# Run unit tests
dotnet test tests/unit/

# Run integration tests
dotnet test tests/integration/
```

## Dependencies

- `Microsoft.AspNetCore.OpenApi` - OpenAPI/Swagger support
- `Swashbuckle.AspNetCore` - Swagger UI generation

## Integration Points

The Backend API communicates with:

- **Gateway**: Receives authenticated requests
- **Engine**: Delegates semantic kernel operations
- **Database**: Persists application data via connection pooling
- **Redis**: Session and cache management

## Resource Limits

| Resource | Production | Development |
| -------- | ---------- | ----------- |
| CPU      | 1.0        | 2.0         |
| Memory   | 512MB      | 1GB         |

## Environment Variables

| Variable                               | Description         | Required |
| -------------------------------------- | ------------------- | -------- |
| `ASPNETCORE_ENVIRONMENT`               | Runtime environment | No       |
| `ConnectionStrings__DefaultConnection` | Database connection | Yes      |
| `Redis__ConnectionString`              | Redis connection    | Yes      |

## Troubleshooting

### Common Issues

1. **Connection Refused**

   - Ensure database and Redis services are running
   - Check network configuration in docker-compose.yml

2. **Health Check Failing**

   - Verify service is listening on correct port
   - Check application logs for startup errors

3. **Swagger Not Loading**
   - Only available in Development environment
   - Set `ASPNETCORE_ENVIRONMENT=Development`

## Related Documentation

- [Architecture Overview](../../ARCHITECTURE.md)
- [Development Guide](../../DEVELOPMENT.md)
- [Gateway API](../gateway/README.md)
- [Engine Service](../engine/README.md)
