using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace SemanticKernelApp.Engine.Factories;

/// <summary>
/// Factory for creating and managing vector store connections.
/// </summary>
public class VectorStoreFactory
{
    private readonly ILogger<VectorStoreFactory> _logger;
    private readonly string _vectorStoreUrl;

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreFactory"/> class.
    /// </summary>
    /// <param name="logger">The logger for diagnostic information.</param>
    /// <param name="vectorStoreUrl">The URL of the vector store service.</param>
    /// <exception cref="ArgumentNullException">Thrown when logger is null.</exception>
    public VectorStoreFactory(ILogger<VectorStoreFactory> logger, string vectorStoreUrl = "http://vector:6333")
    {
        ArgumentNullException.ThrowIfNull(logger);

        _logger = logger;
        _vectorStoreUrl = vectorStoreUrl ?? "http://vector:6333";
    }

    /// <summary>
    /// Creates a vector store client for Qdrant.
    /// </summary>
    /// <returns>A new Qdrant vector store client instance.</returns>
    public IVectorStoreClient CreateQdrantClient()
    {
        _logger.LogInformation("Creating Qdrant client with URL: {Url}", _vectorStoreUrl);

        return new QdrantVectorStoreClient(_vectorStoreUrl, _logger);
    }

    /// <summary>
    /// Gets the configured collection name for embeddings.
    /// </summary>
    /// <returns>The collection name for storing embeddings.</returns>
    public string GetEmbeddingsCollectionName() => "embeddings";

    /// <summary>
    /// Gets the vector dimensions for the embedding model.
    /// </summary>
    /// <returns>The number of dimensions in embedding vectors.</returns>
    public int GetVectorDimensions() => 1536;
}

/// <summary>
/// Interface for vector store operations.
/// </summary>
public interface IVectorStoreClient
{
    /// <summary>
    /// Checks if a collection exists in the vector store.
    /// </summary>
    /// <param name="collectionName">The name of the collection to check.</param>
    /// <param name="cancellationToken">Cancellation token to cancel the operation.</param>
    /// <returns>A task representing the asynchronous operation with a boolean indicating existence.</returns>
    Task<bool> CollectionExistsAsync(string collectionName, CancellationToken cancellationToken = default);

    /// <summary>
    /// Creates a new collection in the vector store.
    /// </summary>
    /// <param name="collectionName">The name of the collection to create.</param>
    /// <param name="dimensions">The number of dimensions for vectors in this collection.</param>
    /// <param name="cancellationToken">Cancellation token to cancel the operation.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    Task CreateCollectionAsync(string collectionName, int dimensions, CancellationToken cancellationToken = default);

    /// <summary>
    /// Upserts a vector into the collection.
    /// </summary>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="vector">The vector to upsert.</param>
    /// <param name="payload">The payload associated with the vector.</param>
    /// <param name="cancellationToken">Cancellation token to cancel the operation.</param>
    /// <returns>A task representing the asynchronous operation with the point ID.</returns>
    Task<string> UpsertVectorAsync(string collectionName, float[] vector, object payload, CancellationToken cancellationToken = default);

    /// <summary>
    /// Searches for similar vectors in the collection.
    /// </summary>
    /// <param name="collectionName">The name of the collection to search.</param>
    /// <param name="queryVector">The query vector to find similarities for.</param>
    /// <param name="limit">The maximum number of results to return.</param>
    /// <param name="cancellationToken">Cancellation token to cancel the operation.</param>
    /// <returns>A task representing the asynchronous operation with the search results.</returns>
    Task<IEnumerable<SearchResult>> SearchAsync(string collectionName, float[] queryVector, int limit = 10, CancellationToken cancellationToken = default);
}

/// <summary>
/// Qdrant vector store client implementation.
/// </summary>
public class QdrantVectorStoreClient : IVectorStoreClient
{
    private readonly string _url;
    private readonly ILogger _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreClient"/> class.
    /// </summary>
    /// <param name="url">The URL of the Qdrant service.</param>
    /// <param name="logger">The logger for diagnostic information.</param>
    /// <exception cref="ArgumentNullException">Thrown when url or logger is null.</exception>
    public QdrantVectorStoreClient(string url, ILogger logger)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(url);
        ArgumentNullException.ThrowIfNull(logger);

        _url = url;
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<bool> CollectionExistsAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(collectionName);

        _logger.LogInformation("Checking if collection exists: {Collection}", collectionName);

        using var httpClient = new HttpClient();
        try
        {
            var response = await httpClient
                .GetAsync($"{_url}/collections/{collectionName}", cancellationToken)
                .ConfigureAwait(false);

            return response.IsSuccessStatusCode;
        }
        catch (HttpRequestException ex)
        {
            _logger.LogWarning(ex, "Failed to check collection existence: {Collection}", collectionName);
            return false;
        }
        catch (TaskCanceledException)
        {
            _logger.LogWarning("Collection existence check was cancelled: {Collection}", collectionName);
            return false;
        }
    }

    /// <inheritdoc />
    public async Task CreateCollectionAsync(string collectionName, int dimensions, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(collectionName);

        if (dimensions <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(dimensions), "Dimensions must be greater than zero.");
        }

        _logger.LogInformation("Creating collection: {Collection} with dimensions: {Dimensions}", collectionName, dimensions);

        using var httpClient = new HttpClient();
        var payload = new
        {
            vectors = new
            {
                size = dimensions,
                distance = "Cosine"
            }
        };

        var content = new StringContent(
            JsonSerializer.Serialize(payload),
            System.Text.Encoding.UTF8,
            "application/json");

        var response = await httpClient
            .PutAsync($"{_url}/collections/{collectionName}", content, cancellationToken)
            .ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        _logger.LogInformation("Successfully created collection: {Collection}", collectionName);
    }

    /// <inheritdoc />
    public async Task<string> UpsertVectorAsync(string collectionName, float[] vector, object payload, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(collectionName);
        ArgumentNullException.ThrowIfNull(vector);
        ArgumentNullException.ThrowIfNull(payload);

        _logger.LogInformation("Upserting vector to collection: {Collection}", collectionName);

        var pointId = Guid.NewGuid().ToString();
        using var httpClient = new HttpClient();

        var requestPayload = new
        {
            points = new[]
            {
                new
                {
                    id = pointId,
                    vector,
                    payload
                }
            }
        };

        var content = new StringContent(
            JsonSerializer.Serialize(requestPayload),
            System.Text.Encoding.UTF8,
            "application/json");

        var response = await httpClient
            .PutAsync($"{_url}/collections/{collectionName}/points?wait=true", content, cancellationToken)
            .ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        _logger.LogInformation("Successfully upserted vector with ID: {PointId}", pointId);
        return pointId;
    }

    /// <inheritdoc />
    public async Task<IEnumerable<SearchResult>> SearchAsync(string collectionName, float[] queryVector, int limit = 10, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(collectionName);
        ArgumentNullException.ThrowIfNull(queryVector);

        if (limit <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(limit), "Limit must be greater than zero.");
        }

        _logger.LogInformation("Searching in collection: {Collection} with limit: {Limit}", collectionName, limit);

        using var httpClient = new HttpClient();

        var requestPayload = new
        {
            vector = queryVector,
            limit,
            with_payload = true
        };

        var content = new StringContent(
            JsonSerializer.Serialize(requestPayload),
            System.Text.Encoding.UTF8,
            "application/json");

        var response = await httpClient
            .PostAsync($"{_url}/collections/{collectionName}/points/search", content, cancellationToken)
            .ConfigureAwait(false);

        response.EnsureSuccessStatusCode();

        var responseBody = await response.Content
            .ReadAsStringAsync(cancellationToken)
            .ConfigureAwait(false);

        var result = JsonDocument.Parse(responseBody);

        var searchResults = result.RootElement.GetProperty("result").EnumerateArray()
            .Select(item => new SearchResult(
                item.GetProperty("id").GetString() ?? string.Empty,
                item.GetProperty("score").GetSingle(),
                item.GetProperty("payload")
            ))
            .ToList();

        _logger.LogInformation("Found {Count} results in collection: {Collection}", searchResults.Count, collectionName);
        return searchResults;
    }
}

/// <summary>
/// Represents a search result from the vector store.
/// </summary>
/// <param name="Id">The unique identifier of the result.</param>
/// <param name="Score">The similarity score of the result.</param>
/// <param name="Payload">The payload associated with the result.</param>
public record SearchResult(string Id, float Score, object Payload);
