using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace SemanticKernelApp.Engine.Factories;

/// <summary>
/// Factory for creating and managing embeddings service connections.
/// </summary>
public class EmbeddingsFactory
{
    private readonly ILogger<EmbeddingsFactory> _logger;
    private readonly HttpClient _httpClient;
    private readonly string _embeddingsServiceUrl;

    /// <summary>
    /// Initializes a new instance of the <see cref="EmbeddingsFactory"/> class.
    /// </summary>
    /// <param name="logger">The logger for diagnostic information.</param>
    /// <param name="httpClient">The HTTP client for making requests.</param>
    /// <param name="embeddingsServiceUrl">The URL of the embeddings service.</param>
    /// <exception cref="ArgumentNullException">Thrown when logger or httpClient is null.</exception>
    public EmbeddingsFactory(
        ILogger<EmbeddingsFactory> logger,
        HttpClient httpClient,
        string embeddingsServiceUrl = "http://embeddings:8001")
    {
        ArgumentNullException.ThrowIfNull(logger);
        ArgumentNullException.ThrowIfNull(httpClient);

        _logger = logger;
        _httpClient = httpClient;
        _embeddingsServiceUrl = embeddingsServiceUrl ?? "http://embeddings:8001";
    }

    /// <summary>
    /// Generates embeddings for the given text.
    /// </summary>
    /// <param name="text">The text to generate embeddings for.</param>
    /// <param name="cancellationToken">Cancellation token to cancel the operation.</param>
    /// <returns>A task representing the asynchronous operation with the embedding vector.</returns>
    /// <exception cref="ArgumentNullException">Thrown when text is null.</exception>
    /// <exception cref="HttpRequestException">Thrown when the HTTP request fails.</exception>
    public async Task<float[]> GenerateEmbeddingAsync(
        string text,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(text);

        _logger.LogInformation("Generating embedding for text of length: {Length}", text.Length);

        try
        {
            var request = new EmbeddingRequest { Text = text };
            var response = await _httpClient
                .PostAsJsonAsync($"{_embeddingsServiceUrl}/api/embeddings", request, cancellationToken)
                .ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            var result = await response.Content
                .ReadFromJsonAsync<EmbeddingResponse>(cancellationToken: cancellationToken)
                .ConfigureAwait(false);

            return result?.Embedding ?? Array.Empty<float>();
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "HTTP request failed while generating embedding");
            throw;
        }
        catch (TaskCanceledException ex) when (ex.CancellationToken == cancellationToken)
        {
            _logger.LogWarning("Embedding generation was cancelled");
            throw;
        }
    }

    /// <summary>
    /// Generates embeddings for multiple texts in batch.
    /// </summary>
    /// <param name="texts">The texts to generate embeddings for.</param>
    /// <param name="cancellationToken">Cancellation token to cancel the operation.</param>
    /// <returns>A task representing the asynchronous operation with the embedding vectors.</returns>
    /// <exception cref="ArgumentNullException">Thrown when texts is null.</exception>
    /// <exception cref="HttpRequestException">Thrown when the HTTP request fails.</exception>
    public async Task<IEnumerable<float[]>> GenerateEmbeddingsBatchAsync(
        IEnumerable<string> texts,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(texts);

        var textArray = texts.ToArray();
        _logger.LogInformation("Generating embeddings for batch of {Count} texts", textArray.Length);

        try
        {
            var request = new BatchEmbeddingRequest { Texts = textArray };
            var response = await _httpClient
                .PostAsJsonAsync($"{_embeddingsServiceUrl}/api/embeddings/batch", request, cancellationToken)
                .ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            var result = await response.Content
                .ReadFromJsonAsync<BatchEmbeddingResponse>(cancellationToken: cancellationToken)
                .ConfigureAwait(false);

            return result?.Embeddings ?? Enumerable.Empty<float[]>();
        }
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "HTTP request failed while generating batch embeddings");
            throw;
        }
        catch (TaskCanceledException ex) when (ex.CancellationToken == cancellationToken)
        {
            _logger.LogWarning("Batch embedding generation was cancelled");
            throw;
        }
    }

    /// <summary>
    /// Checks the health of the embeddings service.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token to cancel the operation.</param>
    /// <returns>A task representing the asynchronous operation with a boolean indicating service health.</returns>
    public async Task<bool> IsHealthyAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _httpClient
                .GetAsync($"{_embeddingsServiceUrl}/health", cancellationToken)
                .ConfigureAwait(false);

            return response.IsSuccessStatusCode;
        }
        catch (HttpRequestException ex)
        {
            _logger.LogWarning(ex, "Health check failed for embeddings service");
            return false;
        }
        catch (TaskCanceledException)
        {
            return false;
        }
    }
}

/// <summary>
/// Represents a request to generate embeddings for a single text.
/// </summary>
public record EmbeddingRequest
{
    /// <summary>
    /// Gets the text to generate embeddings for.
    /// </summary>
    public string Text { get; init; } = string.Empty;
}

/// <summary>
/// Represents a response containing generated embeddings.
/// </summary>
public record EmbeddingResponse
{
    /// <summary>
    /// Gets the generated embedding vector.
    /// </summary>
    public float[] Embedding { get; init; } = Array.Empty<float>();
}

/// <summary>
/// Represents a request to generate embeddings for multiple texts.
/// </summary>
public record BatchEmbeddingRequest
{
    /// <summary>
    /// Gets the texts to generate embeddings for.
    /// </summary>
    public string[] Texts { get; init; } = Array.Empty<string>();
}

/// <summary>
/// Represents a response containing batch generated embeddings.
/// </summary>
public record BatchEmbeddingResponse
{
    /// <summary>
    /// Gets the generated embedding vectors.
    /// </summary>
    public float[][] Embeddings { get; init; } = Array.Empty<float[]>();
}
