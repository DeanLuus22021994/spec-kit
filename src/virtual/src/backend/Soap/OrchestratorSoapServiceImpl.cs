// -----------------------------------------------------------------------
// <copyright file="OrchestratorSoapServiceImpl.cs" company="SemanticKernelApp">
// Copyright (c) SemanticKernelApp. All rights reserved.
// </copyright>
// -----------------------------------------------------------------------

using System.Diagnostics;
using Microsoft.Extensions.Logging;

namespace SemanticKernelApp.Backend.Soap;

/// <summary>
/// Implementation of the Orchestrator SOAP Service.
/// Provides WSDL-compliant operations for 3rd party integrations.
/// </summary>
public class OrchestratorSoapServiceImpl : IOrchestratorSoapService
{
    private readonly ILogger<OrchestratorSoapServiceImpl> _logger;
    private readonly ITaskOrchestrator _orchestrator;
    private readonly IMetricsService _metricsService;
    private static readonly DateTime _startTime = DateTime.UtcNow;

    /// <summary>
    /// Initializes a new instance of the <see cref="OrchestratorSoapServiceImpl"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="orchestrator">The task orchestrator.</param>
    /// <param name="metricsService">The metrics service.</param>
    public OrchestratorSoapServiceImpl(
        ILogger<OrchestratorSoapServiceImpl> logger,
        ITaskOrchestrator orchestrator,
        IMetricsService metricsService)
    {
        _logger = logger;
        _orchestrator = orchestrator;
        _metricsService = metricsService;
    }

    /// <inheritdoc />
    public async Task<ExecuteTaskResponse> ExecuteTaskAsync(ExecuteTaskRequest request)
    {
        var stopwatch = Stopwatch.StartNew();
        var traceId = Activity.Current?.TraceId.ToString() ?? Guid.NewGuid().ToString("N");

        _logger.LogInformation(
            "SOAP ExecuteTask: TaskId={TaskId}, Type={TaskType}, Priority={Priority}, TraceId={TraceId}",
            request.TaskId, request.TaskType, request.Priority, traceId);

        try
        {
            var result = await _orchestrator.ExecuteAsync(
                request.TaskId,
                request.TaskType,
                request.Payload,
                request.Priority,
                request.TimeoutMs,
                request.CorrelationId ?? traceId);

            stopwatch.Stop();
            await _metricsService.RecordTaskExecutionAsync(request.TaskType, stopwatch.ElapsedMilliseconds, true);

            return new ExecuteTaskResponse
            {
                TaskId = request.TaskId,
                Status = "Completed",
                Result = result.ResultPayload,
                ExecutionTimeMs = stopwatch.ElapsedMilliseconds,
                TraceId = traceId,
                AgentTrace = result.AgentTrace,
                Timestamp = DateTime.UtcNow
            };
        }
        catch (TaskCanceledException)
        {
            stopwatch.Stop();
            await _metricsService.RecordTaskExecutionAsync(request.TaskType, stopwatch.ElapsedMilliseconds, false);

            return new ExecuteTaskResponse
            {
                TaskId = request.TaskId,
                Status = "Timeout",
                ExecutionTimeMs = stopwatch.ElapsedMilliseconds,
                TraceId = traceId,
                ErrorMessage = $"Task execution timed out after {request.TimeoutMs}ms",
                Timestamp = DateTime.UtcNow
            };
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "SOAP ExecuteTask failed: TaskId={TaskId}", request.TaskId);
            await _metricsService.RecordTaskExecutionAsync(request.TaskType, stopwatch.ElapsedMilliseconds, false);

            return new ExecuteTaskResponse
            {
                TaskId = request.TaskId,
                Status = "Failed",
                ExecutionTimeMs = stopwatch.ElapsedMilliseconds,
                TraceId = traceId,
                ErrorMessage = ex.Message,
                Timestamp = DateTime.UtcNow
            };
        }
    }

    /// <inheritdoc />
    public async Task<GetTaskStatusResponse> GetTaskStatusAsync(GetTaskStatusRequest request)
    {
        _logger.LogDebug("SOAP GetTaskStatus: TaskId={TaskId}", request.TaskId);

        var status = await _orchestrator.GetStatusAsync(request.TaskId);

        return new GetTaskStatusResponse
        {
            TaskId = request.TaskId,
            Status = status.Status,
            ProgressPercent = status.ProgressPercent,
            CurrentStep = status.CurrentStep,
            StartTime = status.StartTime,
            EstimatedCompletion = status.EstimatedCompletion
        };
    }

    /// <inheritdoc />
    public async Task<CancelTaskResponse> CancelTaskAsync(CancelTaskRequest request)
    {
        _logger.LogInformation("SOAP CancelTask: TaskId={TaskId}, Reason={Reason}", request.TaskId, request.Reason);

        var cancelled = await _orchestrator.CancelAsync(request.TaskId, request.Reason);

        return new CancelTaskResponse
        {
            TaskId = request.TaskId,
            Cancelled = cancelled,
            Message = cancelled
                ? "Task cancelled successfully"
                : "Task could not be cancelled (may have already completed)"
        };
    }

    /// <inheritdoc />
    public async Task<HealthCheckResponse> HealthCheckAsync()
    {
        _logger.LogDebug("SOAP HealthCheck invoked");

        var dependencies = await _orchestrator.CheckDependenciesAsync();

        return new HealthCheckResponse
        {
            Healthy = dependencies.All(d => d.Healthy),
            Version = "1.0.0",
            UptimeSeconds = (long)(DateTime.UtcNow - _startTime).TotalSeconds,
            Dependencies = dependencies.Select(d => new DependencyStatus
            {
                Name = d.Name,
                Healthy = d.Healthy,
                LatencyMs = d.LatencyMs
            }).ToList(),
            Timestamp = DateTime.UtcNow
        };
    }

    /// <inheritdoc />
    public async Task<AgentMetricsResponse> GetAgentMetricsAsync()
    {
        _logger.LogDebug("SOAP GetAgentMetrics invoked");

        var metrics = await _metricsService.GetAgentMetricsAsync();

        return new AgentMetricsResponse
        {
            TotalTasksProcessed = metrics.TotalTasksProcessed,
            ActiveTasks = metrics.ActiveTasks,
            SuccessRate = metrics.SuccessRate,
            AvgExecutionTimeMs = metrics.AvgExecutionTimeMs,
            Agents = metrics.Agents.Select(a => new AgentMetric
            {
                AgentName = a.Name,
                Status = a.Status,
                TasksProcessed = a.TasksProcessed,
                AvgLatencyMs = a.AvgLatencyMs,
                ErrorCount = a.ErrorCount
            }).ToList(),
            Timestamp = DateTime.UtcNow
        };
    }

    /// <inheritdoc />
    public async Task<BatchTaskResponse> SubmitBatchAsync(BatchTaskRequest request)
    {
        _logger.LogInformation(
            "SOAP SubmitBatch: BatchId={BatchId}, TaskCount={TaskCount}, Parallel={Parallel}",
            request.BatchId, request.Tasks?.Count ?? 0, request.Parallel);

        if (request.Tasks == null || request.Tasks.Count == 0)
        {
            return new BatchTaskResponse
            {
                BatchId = request.BatchId,
                TotalTasks = 0,
                AcceptedTasks = 0,
                Status = "Empty"
            };
        }

        var acceptedCount = await _orchestrator.SubmitBatchAsync(
            request.BatchId,
            request.Tasks.Select(t => (t.TaskId, t.TaskType, t.Payload, t.Priority)).ToList(),
            request.Parallel,
            request.StopOnError);

        return new BatchTaskResponse
        {
            BatchId = request.BatchId,
            TotalTasks = request.Tasks.Count,
            AcceptedTasks = acceptedCount,
            Status = "Accepted",
            EstimatedCompletion = DateTime.UtcNow.AddMinutes(request.Tasks.Count * 0.5)
        };
    }
}

// ============================================================================
// Supporting Interfaces (to be implemented by orchestration layer)
// ============================================================================

/// <summary>
/// Interface for task orchestration operations.
/// </summary>
public interface ITaskOrchestrator
{
    /// <summary>
    /// Executes a task asynchronously.
    /// </summary>
    Task<TaskExecutionResult> ExecuteAsync(
        string taskId,
        string taskType,
        string payload,
        int priority,
        int timeoutMs,
        string correlationId);

    /// <summary>
    /// Gets the status of a task.
    /// </summary>
    Task<TaskStatusResult> GetStatusAsync(string taskId);

    /// <summary>
    /// Cancels a task.
    /// </summary>
    Task<bool> CancelAsync(string taskId, string? reason);

    /// <summary>
    /// Checks the health of dependencies.
    /// </summary>
    Task<IEnumerable<DependencyCheckResult>> CheckDependenciesAsync();

    /// <summary>
    /// Submits a batch of tasks.
    /// </summary>
    Task<int> SubmitBatchAsync(
        string batchId,
        IList<(string TaskId, string TaskType, string Payload, int Priority)> tasks,
        bool parallel,
        bool stopOnError);
}

/// <summary>
/// Interface for metrics service.
/// </summary>
public interface IMetricsService
{
    /// <summary>
    /// Records task execution metrics.
    /// </summary>
    Task RecordTaskExecutionAsync(string taskType, long executionTimeMs, bool success);

    /// <summary>
    /// Gets agent metrics.
    /// </summary>
    Task<AgentMetricsResult> GetAgentMetricsAsync();
}

/// <summary>
/// Result of task execution.
/// </summary>
public record TaskExecutionResult(
    string? ResultPayload,
    List<string>? AgentTrace);

/// <summary>
/// Result of task status check.
/// </summary>
public record TaskStatusResult(
    string Status,
    int ProgressPercent,
    string? CurrentStep,
    DateTime? StartTime,
    DateTime? EstimatedCompletion);

/// <summary>
/// Result of dependency health check.
/// </summary>
public record DependencyCheckResult(
    string Name,
    bool Healthy,
    long LatencyMs);

/// <summary>
/// Result of agent metrics query.
/// </summary>
public record AgentMetricsResult(
    long TotalTasksProcessed,
    int ActiveTasks,
    double SuccessRate,
    double AvgExecutionTimeMs,
    IEnumerable<AgentMetricResult> Agents);

/// <summary>
/// Individual agent metric result.
/// </summary>
public record AgentMetricResult(
    string Name,
    string Status,
    long TasksProcessed,
    double AvgLatencyMs,
    int ErrorCount);
