# Learning: Library vs Executable Container Architecture

**Date:** November 24, 2025
**Context:** Business/Engine Service Restart Loop
**Severity:** 🔴 CRITICAL BUG

---

## The Problem

Business and Engine services restarting every 2-3 seconds:

```
dotnet watch ❌ The project file '/src/business/business.csproj' does not exist
```

Dockerfile had:

```dockerfile
ENTRYPOINT ["dotnet", "business.dll"]
```

---

## Root Cause

**Business and Engine are LIBRARY projects:**

- No `Program.cs` file
- No `Main()` method
- `OutputType=Library` in .csproj
- AssemblyName mismatch (BusinessLayer vs business.dll)

**Cannot execute a library as standalone application.**

---

## The Fix

Changed from executable to persistent library container:

```dockerfile
# REMOVED: ENTRYPOINT ["dotnet", "business.dll"]
CMD ["tail", "-f", "/dev/null"]
```

**Purpose:** Keep container alive for other services to reference via Docker networking.

---

## What We Learned

### Project Type Determines Container Pattern

| Type           | Has Main() | Dockerfile Pattern                 | Use Case                   |
| -------------- | ---------- | ---------------------------------- | -------------------------- |
| **Executable** | ✅ Yes     | `ENTRYPOINT ["dotnet", "app.dll"]` | Backend, Gateway, Frontend |
| **Library**    | ❌ No      | `CMD ["tail", "-f", "/dev/null"]`  | Business, Engine           |

### Library Containers Serve Different Purpose

Not standalone applications—they provide:

- Shared code/assemblies
- Service references via Docker networking
- Potential for inter-service DLL sharing (future)

---

## Questions Raised

**Do we even need Business/Engine as separate containers?**

- Could be NuGet packages referenced in Backend/Gateway
- Current architecture: Over-containerization?
- Trade-off: Isolation vs complexity

**Action:** Marked as HIGH PRIORITY pain point for future architecture review.

---

## Applied Knowledge

1. Always check `.csproj` for `OutputType` before creating Dockerfile
2. Library projects need different container strategy
3. `tail -f /dev/null` keeps container alive without executing code
4. Container architecture must match project architecture
