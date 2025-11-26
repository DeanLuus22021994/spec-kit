// Copyright (c) Semantic Kernel App. All rights reserved.

using Backend.Services.Caching;
using StackExchange.Redis;

namespace Backend.Extensions;

/// <summary>
/// Extension methods for registering cache services.
/// </summary>
public static class CacheExtensions
{
    /// <summary>
    /// Adds Redis caching services to the service collection.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="connectionString">The Redis connection string.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddRedisCaching(this IServiceCollection services, string connectionString)
    {
        ArgumentException.ThrowIfNullOrEmpty(connectionString);

        services.AddSingleton<IConnectionMultiplexer>(_ =>
            ConnectionMultiplexer.Connect(connectionString));

        services.AddSingleton<ICacheService, RedisCacheService>();
        services.AddSingleton<CacheServiceFactory>();

        return services;
    }

    /// <summary>
    /// Adds Redis caching services to the service collection using configuration.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="configuration">The configuration.</param>
    /// <param name="sectionName">The configuration section name for Redis settings.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddRedisCaching(
        this IServiceCollection services,
        IConfiguration configuration,
        string sectionName = "Redis")
    {
        var connectionString = configuration.GetConnectionString(sectionName)
            ?? configuration[$"{sectionName}:ConnectionString"]
            ?? throw new InvalidOperationException($"Redis connection string not found in configuration section '{sectionName}'");

        return services.AddRedisCaching(connectionString);
    }

    /// <summary>
    /// Adds Redis caching services with custom configuration options.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="configureOptions">Action to configure Redis options.</param>
    /// <returns>The service collection for chaining.</returns>
    public static IServiceCollection AddRedisCaching(
        this IServiceCollection services,
        Action<ConfigurationOptions> configureOptions)
    {
        ArgumentNullException.ThrowIfNull(configureOptions);

        var options = new ConfigurationOptions();
        configureOptions(options);

        services.AddSingleton<IConnectionMultiplexer>(_ =>
            ConnectionMultiplexer.Connect(options));

        services.AddSingleton<ICacheService, RedisCacheService>();
        services.AddSingleton<CacheServiceFactory>();

        return services;
    }
}
