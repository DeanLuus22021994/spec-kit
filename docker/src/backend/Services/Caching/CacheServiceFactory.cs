// Copyright (c) Semantic Kernel App. All rights reserved.

namespace Backend.Services.Caching;

/// <summary>
/// Factory for creating cache service instances.
/// </summary>
public class CacheServiceFactory
{
    private readonly ICacheService _cacheService;

    /// <summary>
    /// Initializes a new instance of the <see cref="CacheServiceFactory"/> class.
    /// </summary>
    /// <param name="cacheService">The cache service instance.</param>
    public CacheServiceFactory(ICacheService cacheService)
    {
        ArgumentNullException.ThrowIfNull(cacheService);
        _cacheService = cacheService;
    }

    /// <summary>
    /// Gets the cache service instance.
    /// </summary>
    /// <returns>The cache service.</returns>
    public ICacheService GetCacheService() => _cacheService;

    /// <summary>
    /// Creates a new scoped cache key with the given prefix.
    /// </summary>
    /// <param name="prefix">The prefix for the cache key.</param>
    /// <param name="key">The cache key.</param>
    /// <returns>The scoped cache key.</returns>
    public static string CreateScopedKey(string prefix, string key) => $"{prefix}:{key}";
}
