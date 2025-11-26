# Learning: .NET Tool Versioning Doesn't Follow SDK Versioning

**Date:** November 24, 2025
**Context:** dotnet-tools.json Alignment Failure
**Severity:** 🟡 MODERATE - Build Breaking

---

## The Assumption (WRONG)

"We have .NET SDK 10.0, so all tools should be v10.0"

Updated all tools to v10.0 → **dotnet tool restore FAILED**

---

## The Reality

.NET tool ecosystem has **independent versioning** from SDK:

### Tools at v10.0 (3 tools)

- dotnet-ef
- dotnet-monitor
- microsoft.dotnet-openapi

### Tools at v9.0 (1 tool)

- dotnet-aspnet-codegenerator

### Tools at v9.0.652701 (6 tools)

- dotnet-trace, counters, dump, gcdump, sos, symbol (diagnostics suite)

### Tools at v8.0 (1 tool)

- microsoft.dotnet-httprepl

### Tools with custom versioning (9 tools)

- dotnet-format: **v5.1.250801** (not v5.0, v6.0, or v10.0)
- dotnet-coverage: **v18.1.0** (totally independent)
- csharpier: **v1.2.1** (own versioning scheme)

---

## What Broke

```bash
dotnet tool restore
# Error: Version 10.0.0 of package dotnet-aspnet-codegenerator is not found
# Error: Version 10.0.0 of package microsoft.dotnet-httprepl is not found
```

NuGet doesn't have these versions. Tools lag behind SDK releases.

---

## The Fix

**Check each tool's ACTUAL latest version:**

```bash
dotnet tool search dotnet-aspnet-codegenerator
# Result: dotnet-aspnet-codegenerator 9.0.0
```

Repeated for all 20 tools → updated to real available versions.

---

## What We Learned

1. **SDK version ≠ Tool version** - No 1:1 relationship
2. **Always verify NuGet availability** before setting tool versions
3. **`dotnet tool search` is authoritative** - Use it, don't guess
4. **Tool ecosystems move independently** - Different release cadences
5. **Command names matter** - csharpier vs dotnet-csharpier

---

## New Workflow

**Before updating tool versions:**

1. Check current SDK: `dotnet --version`
2. Search each tool: `dotnet tool search <tool-name>`
3. Verify version exists in NuGet
4. Update dotnet-tools.json with ACTUAL latest
5. Test restore: `dotnet tool restore`

**Don't assume version alignment.**

---

## Saved By

- Systematic checking of each tool (20 searches)
- Error messages that explicitly stated missing versions
- Understanding that tool ecosystem is decentralized
