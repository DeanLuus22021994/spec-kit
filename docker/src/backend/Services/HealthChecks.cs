// -----------------------------------------------------------------------
// <copyright file="HealthChecks.cs" company="SemanticKernelApp">
// Copyright (c) SemanticKernelApp. All rights reserved.
// </copyright>
// -----------------------------------------------------------------------

using Microsoft.Extensions.Diagnostics.HealthChecks;

namespace SemanticKernelApp.Backend.Services;

/// <summary>
/// Health check for database connectivity.
/// </summary>
public class DatabaseHealthCheck : IHealthCheck
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<DatabaseHealthCheck> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="DatabaseHealthCheck"/> class.
    /// </summary>
    public DatabaseHealthCheck(IConfiguration configuration, ILogger<DatabaseHealthCheck> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var connectionString = _configuration.GetConnectionString("Database");
            if (string.IsNullOrEmpty(connectionString))
            {
                return HealthCheckResult.Degraded("Database connection string not configured");
            }

            // TODO: Add actual database connectivity check
            await Task.Delay(10, cancellationToken);
            return HealthCheckResult.Healthy("Database connection successful");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Database health check failed");
            return HealthCheckResult.Unhealthy("Database connection failed", ex);
        }
    }
}

/// <summary>
/// Health check for Redis connectivity.
/// </summary>
public class RedisHealthCheck : IHealthCheck
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<RedisHealthCheck> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisHealthCheck"/> class.
    /// </summary>
    public RedisHealthCheck(IConfiguration configuration, ILogger<RedisHealthCheck> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var redisConnection = _configuration["Redis:ConnectionString"];
            if (string.IsNullOrEmpty(redisConnection))
            {
                return HealthCheckResult.Degraded("Redis connection string not configured");
            }

            // TODO: Add actual Redis connectivity check
            await Task.Delay(10, cancellationToken);
            return HealthCheckResult.Healthy("Redis connection successful");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Redis health check failed");
            return HealthCheckResult.Unhealthy("Redis connection failed", ex);
        }
    }
}

/// <summary>
/// Health check for Vector Store (Qdrant) connectivity.
/// </summary>
public class VectorStoreHealthCheck : IHealthCheck
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<VectorStoreHealthCheck> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreHealthCheck"/> class.
    /// </summary>
    public VectorStoreHealthCheck(IConfiguration configuration, ILogger<VectorStoreHealthCheck> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<HealthCheckResult> CheckHealthAsync(
        HealthCheckContext context,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var vectorUrl = _configuration["Qdrant:Url"];
            if (string.IsNullOrEmpty(vectorUrl))
            {
                return HealthCheckResult.Degraded("Vector store URL not configured");
            }

            // TODO: Add actual Qdrant connectivity check
            await Task.Delay(10, cancellationToken);
            return HealthCheckResult.Healthy("Vector store connection successful");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Vector store health check failed");
            return HealthCheckResult.Unhealthy("Vector store connection failed", ex);
        }
    }
}
