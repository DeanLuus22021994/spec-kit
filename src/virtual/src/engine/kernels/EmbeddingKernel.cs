using System;
using Microsoft.SemanticKernel;

namespace SemanticKernelApp.Engine.Kernels;

/// <summary>
/// Kernel for generating and managing embeddings.
/// </summary>
public class EmbeddingKernel
{
    /// <summary>
    /// Gets the underlying Semantic Kernel instance.
    /// </summary>
    public Kernel Instance { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="EmbeddingKernel"/> class.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel instance to wrap.</param>
    /// <exception cref="ArgumentNullException">Thrown when kernel is null.</exception>
    public EmbeddingKernel(Kernel kernel)
    {
        ArgumentNullException.ThrowIfNull(kernel);
        Instance = kernel;
    }
}
