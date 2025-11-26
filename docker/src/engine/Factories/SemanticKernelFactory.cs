using System;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace SemanticKernelApp.Engine.Factories;

/// <summary>
/// Factory for creating and configuring Semantic Kernel instances.
/// </summary>
public class SemanticKernelFactory
{
    private readonly ILogger<SemanticKernelFactory> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="SemanticKernelFactory"/> class.
    /// </summary>
    /// <param name="logger">The logger for diagnostic information.</param>
    /// <exception cref="ArgumentNullException">Thrown when logger is null.</exception>
    public SemanticKernelFactory(ILogger<SemanticKernelFactory> logger)
    {
        ArgumentNullException.ThrowIfNull(logger);
        _logger = logger;
    }

    /// <summary>
    /// Creates a configured Kernel instance for chat operations.
    /// </summary>
    /// <param name="apiKey">The API key for OpenAI services.</param>
    /// <param name="model">The model to use for chat operations. Defaults to "gpt-4".</param>
    /// <returns>A configured Kernel instance.</returns>
    /// <exception cref="ArgumentNullException">Thrown when apiKey is null or empty.</exception>
    public Kernel CreateChatKernel(string apiKey, string model = "gpt-4")
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(apiKey);

        _logger.LogInformation("Creating chat kernel with model: {Model}", model);

        var builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(model, apiKey);

        return builder.Build();
    }

    /// <summary>
    /// Creates a configured Kernel instance for embeddings.
    /// </summary>
    /// <param name="apiKey">The API key for OpenAI services.</param>
    /// <param name="model">The model to use for embeddings. Defaults to "text-embedding-3-small".</param>
    /// <returns>A configured Kernel instance.</returns>
    /// <exception cref="ArgumentNullException">Thrown when apiKey is null or empty.</exception>
    public Kernel CreateEmbeddingKernel(string apiKey, string model = "text-embedding-3-small")
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(apiKey);

        _logger.LogInformation("Creating embedding kernel with model: {Model}", model);

        var builder = Kernel.CreateBuilder();

#pragma warning disable SKEXP0010
        builder.AddOpenAIEmbeddingGenerator(model, apiKey);
#pragma warning restore SKEXP0010

        return builder.Build();
    }

    /// <summary>
    /// Creates a kernel configured for completions.
    /// </summary>
    /// <param name="apiKey">The API key for OpenAI services.</param>
    /// <param name="model">The model to use for completions. Defaults to "gpt-4".</param>
    /// <returns>A configured Kernel instance.</returns>
    /// <exception cref="ArgumentNullException">Thrown when apiKey is null or empty.</exception>
    public Kernel CreateCompletionKernel(string apiKey, string model = "gpt-4")
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(apiKey);

        _logger.LogInformation("Creating completion kernel with model: {Model}", model);

        var builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(model, apiKey);

        return builder.Build();
    }
}
