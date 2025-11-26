# API Documentation

This directory contains API documentation for the Semantic Kernel Application services.

## Services Overview

| Service                     | Port     | Description                     |
| --------------------------- | -------- | ------------------------------- |
| [Backend API](#backend-api) | 5000     | Primary REST API                |
| [Gateway API](#gateway-api) | 8080     | API Gateway with authentication |
| [Engine API](#engine-api)   | Internal | Semantic Kernel processing      |

## Backend API

The Backend API provides RESTful endpoints for application functionality.

### Base URL

- **Development**: `http://localhost:5000`
- **Production**: Via Gateway at `http://localhost:8080/api`

### Authentication

All endpoints (except health) require a valid JWT token:

```http
Authorization: Bearer <token>
```

### Endpoints

#### Health Check

```http
GET /health
```

Returns service health status.

**Response**: `200 OK`

```json
{
  "status": "Healthy"
}
```

#### Swagger Documentation

Interactive API documentation available at:

```
http://localhost:5000/swagger
```

_Note: Only available in Development environment._

## Gateway API

The Gateway handles authentication, routing, and rate limiting.

### Base URL

- **Development**: `http://localhost:8080`
- **Production**: `http://localhost:80` (via Nginx)

### Authentication Endpoints

#### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

**Response**: `200 OK`

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 3600,
  "refreshToken": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

#### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refreshToken": "dGhpcyBpcyBhIHJlZnJlc2g..."
}
```

### Rate Limiting

The Gateway enforces rate limits:

| Tier     | Requests/Minute | Tokens/Day |
| -------- | --------------- | ---------- |
| Free     | 60              | 10,000     |
| Standard | 300             | 100,000    |
| Premium  | 1000            | Unlimited  |

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1640000000
```

## Engine API

The Engine API is internal and accessed through the Backend.

### Semantic Kernel Operations

#### Execute Request

```http
POST /kernel/execute
Content-Type: application/json
Authorization: Bearer <token>

{
  "input": "Summarize this document...",
  "options": {
    "planner": "sequential",
    "maxTokens": 500
  }
}
```

**Response**: `200 OK`

```json
{
  "success": true,
  "result": {
    "output": "Summary: ...",
    "tokensUsed": 150,
    "executionTime": "00:00:01.234"
  }
}
```

#### Memory Operations

**Store Memory**

```http
POST /kernel/memory
Content-Type: application/json
Authorization: Bearer <token>

{
  "collection": "documents",
  "text": "Important information to remember",
  "metadata": {
    "source": "document.pdf",
    "page": 1
  }
}
```

**Search Memory**

```http
GET /kernel/memory/search?collection=documents&query=important&limit=10
Authorization: Bearer <token>
```

## Error Handling

All APIs use consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request body is invalid",
    "details": [
      {
        "field": "input",
        "message": "Input is required"
      }
    ]
  }
}
```

### Error Codes

| Code               | HTTP Status | Description              |
| ------------------ | ----------- | ------------------------ |
| `VALIDATION_ERROR` | 400         | Invalid request data     |
| `UNAUTHORIZED`     | 401         | Missing or invalid token |
| `FORBIDDEN`        | 403         | Insufficient permissions |
| `NOT_FOUND`        | 404         | Resource not found       |
| `RATE_LIMITED`     | 429         | Rate limit exceeded      |
| `INTERNAL_ERROR`   | 500         | Server error             |

## SDKs and Clients

### JavaScript/TypeScript

```typescript
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8080",
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

const response = await api.post("/kernel/execute", {
  input: "Your query here",
});
```

### C# / .NET

```csharp
using var client = new HttpClient();
client.BaseAddress = new Uri("http://localhost:8080");
client.DefaultRequestHeaders.Authorization =
    new AuthenticationHeaderValue("Bearer", token);

var response = await client.PostAsJsonAsync("/kernel/execute", new {
    Input = "Your query here"
});
```

## WebSocket Support

Real-time updates are available via WebSocket:

```javascript
const ws = new WebSocket("ws://localhost:8080/ws");

ws.onopen = () => {
  ws.send(
    JSON.stringify({
      type: "subscribe",
      channel: "execution-status",
    })
  );
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Status update:", data);
};
```

## Related Documentation

- [Architecture Overview](../../ARCHITECTURE.md)
- [Development Guide](../../DEVELOPMENT.md)
- [Backend README](../../src/backend/README.md)
- [Gateway README](../../src/gateway/README.md)
