# Test Service Architecture Documentation

**Version:** 1.0.0
**Date:** November 24, 2025
**Purpose:** Document service types and container patterns for test infrastructure

---

## Service Type Classification

### Executable Services (Standalone Applications)

| Service        | Type                 | Entry Point           | Container Pattern                      | Test Usage             |
| -------------- | -------------------- | --------------------- | -------------------------------------- | ---------------------- |
| **frontend**   | React SPA            | `npm start`           | `CMD ["npm", "start"]`                 | E2E UI testing target  |
| **backend**    | ASP.NET Web API      | `dotnet backend.dll`  | `ENTRYPOINT ["dotnet", "backend.dll"]` | API testing target     |
| **gateway**    | API Gateway          | `dotnet gateway.dll`  | `ENTRYPOINT ["dotnet", "gateway.dll"]` | Routing/auth testing   |
| **embeddings** | FastAPI Service      | `uvicorn main:app`    | `CMD ["uvicorn", "main:app"]`          | Vector/embedding tests |
| **tests**      | Playwright Container | `npx playwright test` | `CMD ["npx", "playwright", "test"]`    | Test execution         |

**Characteristics:**

- ✅ Has `Main()` method or equivalent entry point
- ✅ Can run as standalone application
- ✅ Produces executable output (`.dll`, binary, or script)
- ✅ Listens on network ports (HTTP, TCP, etc.)
- ✅ Suitable for `ENTRYPOINT` or `CMD` directives

---

### Library Services (Shared Components)

| Service      | Type         | Output                     | Container Pattern                 | Test Usage                      |
| ------------ | ------------ | -------------------------- | --------------------------------- | ------------------------------- |
| **business** | .NET Library | `BusinessLayer.dll`        | `CMD ["tail", "-f", "/dev/null"]` | Referenced by integration tests |
| **engine**   | .NET Library | `SemanticKernelEngine.dll` | `CMD ["tail", "-f", "/dev/null"]` | SK functionality testing        |

**Characteristics:**

- ❌ No `Main()` method
- ❌ Cannot run standalone
- ✅ Provides shared code/assemblies
- ✅ Referenced by other projects
- ⚠️ Container kept alive with `tail -f /dev/null`

**Why Containerize Libraries?**

- Docker networking access for future inter-service DLL sharing
- Volume persistence for build artifacts
- Consistent development environment
- Potential future use cases (service mesh, shared volumes)

---

### Support Services (Infrastructure)

| Service      | Type          | Purpose          | Test Usage                  |
| ------------ | ------------- | ---------------- | --------------------------- |
| **database** | PostgreSQL 16 | Data persistence | Test data storage           |
| **vector**   | Qdrant        | Vector search    | Embedding storage/retrieval |

**Characteristics:**

- Third-party Docker images
- Provide infrastructure services
- No custom code
- Configured via environment variables

---

## Container Anti-Patterns (Lessons from Retro)

### ❌ Anti-Pattern 1: Executing Library Projects

**Problem:**

```dockerfile
# WRONG - business.csproj is OutputType=Library
ENTRYPOINT ["dotnet", "business.dll"]
```

**Error:**

```
dotnet watch ❌ The project file '/src/business/business.csproj' does not exist
Service restarts every 2-3 seconds
```

**Solution:**

```dockerfile
# CORRECT - Keep container alive for networking/volumes
CMD ["tail", "-f", "/dev/null"]
```

### ❌ Anti-Pattern 2: Assuming Project Has Main Method

**Detection:**

```bash
# Check .csproj file
grep "<OutputType>" src/business/business.csproj
# Output: <OutputType>Library</OutputType>

# Library projects will not have Program.cs
test -f src/business/Program.cs || echo "No entry point"
```

**Prevention:**

- Always check `.csproj` for `OutputType` before creating Dockerfile
- Verify `Program.cs` or `Main()` method exists
- Test container locally before adding to docker-compose

### ❌ Anti-Pattern 3: Over-Containerization

**Question:** Do we need Business/Engine as separate containers?

**Alternatives:**

1. **NuGet packages** - Package as libraries, reference in Backend/Gateway
2. **Direct project references** - Add `<ProjectReference>` in consuming projects
3. **Shared volume** - Build to volume, mount in consuming containers

**Trade-offs:**

| Approach            | Isolation | Complexity | Build Time | Best For              |
| ------------------- | --------- | ---------- | ---------- | --------------------- |
| Separate Containers | High      | High       | Slower     | Microservices         |
| NuGet Packages      | Medium    | Medium     | Medium     | Versioned libraries   |
| Project References  | Low       | Low        | Faster     | Monolith/modular apps |

**Current Status:** 🟡 **Marked for future architecture review**

---

## Integration Test Patterns

### Pattern 1: Testing Executable Services

```csharp
// tests/integration-tests/BackendApiTests.cs
[Fact]
public async Task Backend_HealthCheck_ReturnsOk()
{
    var response = await _httpClient.GetAsync("http://backend:80/health");
    Assert.Equal(HttpStatusCode.OK, response.StatusCode);
}
```

**Usage:**

- Direct HTTP calls to service endpoints
- Docker Compose networking (`http://backend:80`)
- Service must be running and healthy

### Pattern 2: Testing Library Services

```csharp
// tests/integration-tests/BusinessLayerTests.cs
[Fact]
public void BusinessLayer_ValidateInput_ReturnsTrueForValidData()
{
    // Option A: Direct DLL reference (if accessible)
    var validator = new InputValidator();
    var result = validator.Validate(testData);
    Assert.True(result);

    // Option B: Test via consuming service (Backend)
    // Make API call that internally uses BusinessLayer
    var response = await _httpClient.PostAsync("http://backend:80/api/validate", content);
    Assert.Equal(HttpStatusCode.OK, response.StatusCode);
}
```

**Usage:**

- Test library functionality via consuming services
- Or add project reference to integration test project
- Avoid trying to execute library containers directly

---

## Validation Checklist

### Before Creating Service Dockerfile

- [ ] Check `.csproj` for `<OutputType>`
  - `Exe` → Executable container with `ENTRYPOINT`
  - `Library` → Persistent container with `tail -f /dev/null`
- [ ] Verify entry point exists (`Program.cs`, `Main()`, or script)
- [ ] Determine if service needs to be containerized
  - Does it provide network service? → Containerize
  - Is it just a shared library? → Consider alternatives
- [ ] Plan integration test strategy
  - Executable → Direct HTTP/TCP testing
  - Library → Test via consuming service or project reference

### Before Adding to docker-compose.yml

- [ ] Document service type in comments
- [ ] Set appropriate `command:` directive
- [ ] Define health check (if executable)
- [ ] Configure depends_on relationships
- [ ] Set up environment variables
- [ ] Add to test network

### Before Writing Integration Tests

- [ ] Understand service type (executable vs library)
- [ ] Choose testing approach (direct vs indirect)
- [ ] Verify service is in docker-compose.test.yml
- [ ] Check service health before testing
- [ ] Use Docker networking URLs (`http://service:port`)

---

## Quick Reference

**Identify Service Type:**

```bash
# Check .csproj
grep -E "<OutputType>|<Project Sdk=" src/*/*.csproj

# List all executables
find src -name "*.csproj" -exec grep -l "<OutputType>Exe</OutputType>" {} \;

# List all libraries
find src -name "*.csproj" -exec grep -l "<OutputType>Library</OutputType>" {} \;
```

**Validate Container Pattern:**

```bash
# Check docker-compose for ENTRYPOINT/CMD
docker-compose -f tests/.config/docker/docker-compose.test.yml config | grep -A 2 "command:"

# Verify container is running
docker-compose -f tests/.config/docker/docker-compose.test.yml ps

# Test library container is alive
docker-compose exec business echo "Container is running"
```

---

## Future Considerations

1. **Consolidate Libraries** - Consider merging business + engine into single library project
2. **NuGet Pipeline** - Set up internal NuGet feed for library versioning
3. **Build Optimization** - Shared build cache between related services
4. **Service Mesh** - If library containers grow, consider service mesh for DLL sharing

**Status:** Documented for architectural review in Sprint Planning
