using System;
using Microsoft.SemanticKernel;

namespace SemanticKernelApp.Engine.Kernels;

/// <summary>
/// Main kernel instance for general-purpose AI operations.
/// </summary>
public class MainKernel
{
    /// <summary>
    /// Gets the underlying Semantic Kernel instance.
    /// </summary>
    public Kernel Instance { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="MainKernel"/> class.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel instance to wrap.</param>
    /// <exception cref="ArgumentNullException">Thrown when kernel is null.</exception>
    public MainKernel(Kernel kernel)
    {
        ArgumentNullException.ThrowIfNull(kernel);
        Instance = kernel;
    }
}
