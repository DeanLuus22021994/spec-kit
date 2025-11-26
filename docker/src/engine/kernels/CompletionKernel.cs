using System;
using Microsoft.SemanticKernel;

namespace SemanticKernelApp.Engine.Kernels;

/// <summary>
/// Kernel optimized for text completion tasks.
/// </summary>
public class CompletionKernel
{
    /// <summary>
    /// Gets the underlying Semantic Kernel instance.
    /// </summary>
    public Kernel Instance { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CompletionKernel"/> class.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel instance to wrap.</param>
    /// <exception cref="ArgumentNullException">Thrown when kernel is null.</exception>
    public CompletionKernel(Kernel kernel)
    {
        ArgumentNullException.ThrowIfNull(kernel);
        Instance = kernel;
    }
}
