using System;
using Microsoft.SemanticKernel;

namespace SemanticKernelApp.Engine.Kernels;

/// <summary>
/// Specialized kernel for chat and conversation operations.
/// </summary>
public class ChatKernel
{
    /// <summary>
    /// Gets the underlying Semantic Kernel instance.
    /// </summary>
    public Kernel Instance { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatKernel"/> class.
    /// </summary>
    /// <param name="kernel">The Semantic Kernel instance to wrap.</param>
    /// <exception cref="ArgumentNullException">Thrown when kernel is null.</exception>
    public ChatKernel(Kernel kernel)
    {
        ArgumentNullException.ThrowIfNull(kernel);
        Instance = kernel;
    }
}
