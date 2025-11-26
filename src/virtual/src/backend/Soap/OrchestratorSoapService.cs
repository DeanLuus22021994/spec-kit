// -----------------------------------------------------------------------
// <copyright file="OrchestratorSoapService.cs" company="SemanticKernelApp">
// Copyright (c) SemanticKernelApp. All rights reserved.
// </copyright>
// -----------------------------------------------------------------------

using System.Runtime.Serialization;
using System.ServiceModel;

namespace SemanticKernelApp.Backend.Soap;

/// <summary>
/// SOAP Service Contract for the Orchestrator Agent.
/// Provides WSDL-compliant interface for 3rd party integrations.
/// Uses SoapCore for ASP.NET Core compatibility.
/// </summary>
[ServiceContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public interface IOrchestratorSoapService
{
    /// <summary>
    /// Executes a task through the orchestration pipeline.
    /// </summary>
    /// <param name="request">The task execution request.</param>
    /// <returns>The task execution response.</returns>
    [OperationContract]
    Task<ExecuteTaskResponse> ExecuteTaskAsync(ExecuteTaskRequest request);

    /// <summary>
    /// Gets the status of an existing task.
    /// </summary>
    /// <param name="request">The task status request.</param>
    /// <returns>The task status response.</returns>
    [OperationContract]
    Task<GetTaskStatusResponse> GetTaskStatusAsync(GetTaskStatusRequest request);

    /// <summary>
    /// Cancels a running task.
    /// </summary>
    /// <param name="request">The cancel task request.</param>
    /// <returns>The cancel task response.</returns>
    [OperationContract]
    Task<CancelTaskResponse> CancelTaskAsync(CancelTaskRequest request);

    /// <summary>
    /// Health check for the orchestrator service.
    /// </summary>
    /// <returns>Health check response.</returns>
    [OperationContract]
    Task<HealthCheckResponse> HealthCheckAsync();

    /// <summary>
    /// Gets agent metrics and statistics.
    /// </summary>
    /// <returns>Agent metrics response.</returns>
    [OperationContract]
    Task<AgentMetricsResponse> GetAgentMetricsAsync();

    /// <summary>
    /// Submits a batch of tasks for processing.
    /// </summary>
    /// <param name="request">The batch request.</param>
    /// <returns>Batch submission response.</returns>
    [OperationContract]
    Task<BatchTaskResponse> SubmitBatchAsync(BatchTaskRequest request);
}

// ============================================================================
// Request/Response Data Contracts
// ============================================================================

/// <summary>
/// Request to execute a task through orchestration.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class ExecuteTaskRequest
{
    /// <summary>Gets or sets the unique task identifier.</summary>
    [DataMember(IsRequired = true, Order = 1)]
    public string TaskId { get; set; } = string.Empty;

    /// <summary>Gets or sets the type of task to execute.</summary>
    [DataMember(IsRequired = true, Order = 2)]
    public string TaskType { get; set; } = string.Empty;

    /// <summary>Gets or sets the task payload as base64 encoded JSON.</summary>
    [DataMember(IsRequired = true, Order = 3)]
    public string Payload { get; set; } = string.Empty;

    /// <summary>Gets or sets the task priority (1-10, default 5).</summary>
    [DataMember(IsRequired = false, Order = 4)]
    public int Priority { get; set; } = 5;

    /// <summary>Gets or sets the timeout in milliseconds.</summary>
    [DataMember(IsRequired = false, Order = 5)]
    public int TimeoutMs { get; set; } = 30000;

    /// <summary>Gets or sets the callback URL for async completion.</summary>
    [DataMember(IsRequired = false, Order = 6)]
    public string? CallbackUrl { get; set; }

    /// <summary>Gets or sets the correlation ID for tracing.</summary>
    [DataMember(IsRequired = false, Order = 7)]
    public string? CorrelationId { get; set; }
}

/// <summary>
/// Response from task execution.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class ExecuteTaskResponse
{
    /// <summary>Gets or sets the task identifier.</summary>
    [DataMember(Order = 1)]
    public string TaskId { get; set; } = string.Empty;

    /// <summary>Gets or sets the execution status.</summary>
    [DataMember(Order = 2)]
    public string Status { get; set; } = string.Empty;

    /// <summary>Gets or sets the result as base64 encoded JSON.</summary>
    [DataMember(Order = 3)]
    public string? Result { get; set; }

    /// <summary>Gets or sets the execution time in milliseconds.</summary>
    [DataMember(Order = 4)]
    public long ExecutionTimeMs { get; set; }

    /// <summary>Gets or sets the trace ID for observability.</summary>
    [DataMember(Order = 5)]
    public string? TraceId { get; set; }

    /// <summary>Gets or sets the agents involved in processing.</summary>
    [DataMember(Order = 6)]
    public List<string>? AgentTrace { get; set; }

    /// <summary>Gets or sets the error message if failed.</summary>
    [DataMember(Order = 7)]
    public string? ErrorMessage { get; set; }

    /// <summary>Gets or sets the timestamp of completion.</summary>
    [DataMember(Order = 8)]
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Request to get task status.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class GetTaskStatusRequest
{
    /// <summary>Gets or sets the task identifier.</summary>
    [DataMember(IsRequired = true, Order = 1)]
    public string TaskId { get; set; } = string.Empty;
}

/// <summary>
/// Response with task status.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class GetTaskStatusResponse
{
    /// <summary>Gets or sets the task identifier.</summary>
    [DataMember(Order = 1)]
    public string TaskId { get; set; } = string.Empty;

    /// <summary>Gets or sets the current status.</summary>
    [DataMember(Order = 2)]
    public string Status { get; set; } = string.Empty;

    /// <summary>Gets or sets the progress percentage (0-100).</summary>
    [DataMember(Order = 3)]
    public int ProgressPercent { get; set; }

    /// <summary>Gets or sets the current step description.</summary>
    [DataMember(Order = 4)]
    public string? CurrentStep { get; set; }

    /// <summary>Gets or sets the start time.</summary>
    [DataMember(Order = 5)]
    public DateTime? StartTime { get; set; }

    /// <summary>Gets or sets the estimated completion time.</summary>
    [DataMember(Order = 6)]
    public DateTime? EstimatedCompletion { get; set; }
}

/// <summary>
/// Request to cancel a task.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class CancelTaskRequest
{
    /// <summary>Gets or sets the task identifier.</summary>
    [DataMember(IsRequired = true, Order = 1)]
    public string TaskId { get; set; } = string.Empty;

    /// <summary>Gets or sets the cancellation reason.</summary>
    [DataMember(IsRequired = false, Order = 2)]
    public string? Reason { get; set; }
}

/// <summary>
/// Response from task cancellation.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class CancelTaskResponse
{
    /// <summary>Gets or sets the task identifier.</summary>
    [DataMember(Order = 1)]
    public string TaskId { get; set; } = string.Empty;

    /// <summary>Gets or sets whether cancellation was successful.</summary>
    [DataMember(Order = 2)]
    public bool Cancelled { get; set; }

    /// <summary>Gets or sets a message about the cancellation.</summary>
    [DataMember(Order = 3)]
    public string? Message { get; set; }
}

/// <summary>
/// Health check response.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class HealthCheckResponse
{
    /// <summary>Gets or sets whether the service is healthy.</summary>
    [DataMember(Order = 1)]
    public bool Healthy { get; set; }

    /// <summary>Gets or sets the service version.</summary>
    [DataMember(Order = 2)]
    public string Version { get; set; } = string.Empty;

    /// <summary>Gets or sets the service uptime in seconds.</summary>
    [DataMember(Order = 3)]
    public long UptimeSeconds { get; set; }

    /// <summary>Gets or sets dependent service statuses.</summary>
    [DataMember(Order = 4)]
    public List<DependencyStatus>? Dependencies { get; set; }

    /// <summary>Gets or sets the check timestamp.</summary>
    [DataMember(Order = 5)]
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Dependency status for health check.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class DependencyStatus
{
    /// <summary>Gets or sets the dependency name.</summary>
    [DataMember(Order = 1)]
    public string Name { get; set; } = string.Empty;

    /// <summary>Gets or sets whether the dependency is healthy.</summary>
    [DataMember(Order = 2)]
    public bool Healthy { get; set; }

    /// <summary>Gets or sets the latency in milliseconds.</summary>
    [DataMember(Order = 3)]
    public long LatencyMs { get; set; }
}

/// <summary>
/// Agent metrics response.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class AgentMetricsResponse
{
    /// <summary>Gets or sets the total tasks processed.</summary>
    [DataMember(Order = 1)]
    public long TotalTasksProcessed { get; set; }

    /// <summary>Gets or sets the active task count.</summary>
    [DataMember(Order = 2)]
    public int ActiveTasks { get; set; }

    /// <summary>Gets or sets the success rate percentage.</summary>
    [DataMember(Order = 3)]
    public double SuccessRate { get; set; }

    /// <summary>Gets or sets the average execution time in milliseconds.</summary>
    [DataMember(Order = 4)]
    public double AvgExecutionTimeMs { get; set; }

    /// <summary>Gets or sets individual agent metrics.</summary>
    [DataMember(Order = 5)]
    public List<AgentMetric>? Agents { get; set; }

    /// <summary>Gets or sets the timestamp.</summary>
    [DataMember(Order = 6)]
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}

/// <summary>
/// Individual agent metric.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class AgentMetric
{
    /// <summary>Gets or sets the agent name.</summary>
    [DataMember(Order = 1)]
    public string AgentName { get; set; } = string.Empty;

    /// <summary>Gets or sets the agent status.</summary>
    [DataMember(Order = 2)]
    public string Status { get; set; } = string.Empty;

    /// <summary>Gets or sets the tasks processed by this agent.</summary>
    [DataMember(Order = 3)]
    public long TasksProcessed { get; set; }

    /// <summary>Gets or sets the average latency.</summary>
    [DataMember(Order = 4)]
    public double AvgLatencyMs { get; set; }

    /// <summary>Gets or sets the error count.</summary>
    [DataMember(Order = 5)]
    public int ErrorCount { get; set; }
}

/// <summary>
/// Batch task request.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class BatchTaskRequest
{
    /// <summary>Gets or sets the batch identifier.</summary>
    [DataMember(Order = 1)]
    public string BatchId { get; set; } = string.Empty;

    /// <summary>Gets or sets the tasks in the batch.</summary>
    [DataMember(Order = 2)]
    public List<ExecuteTaskRequest>? Tasks { get; set; }

    /// <summary>Gets or sets whether to execute in parallel.</summary>
    [DataMember(Order = 3)]
    public bool Parallel { get; set; } = true;

    /// <summary>Gets or sets whether to stop on first error.</summary>
    [DataMember(Order = 4)]
    public bool StopOnError { get; set; } = false;
}

/// <summary>
/// Batch task response.
/// </summary>
[DataContract(Namespace = "http://semantic-kernel.local/orchestrator")]
public class BatchTaskResponse
{
    /// <summary>Gets or sets the batch identifier.</summary>
    [DataMember(Order = 1)]
    public string BatchId { get; set; } = string.Empty;

    /// <summary>Gets or sets the total task count.</summary>
    [DataMember(Order = 2)]
    public int TotalTasks { get; set; }

    /// <summary>Gets or sets the accepted task count.</summary>
    [DataMember(Order = 3)]
    public int AcceptedTasks { get; set; }

    /// <summary>Gets or sets the batch status.</summary>
    [DataMember(Order = 4)]
    public string Status { get; set; } = string.Empty;

    /// <summary>Gets or sets the estimated completion time.</summary>
    [DataMember(Order = 5)]
    public DateTime? EstimatedCompletion { get; set; }
}
