// -----------------------------------------------------------------------
// <copyright file="DefaultTaskOrchestrator.cs" company="SemanticKernelApp">
// Copyright (c) SemanticKernelApp. All rights reserved.
// </copyright>
// -----------------------------------------------------------------------

using System.Collections.Concurrent;
using SemanticKernelApp.Backend.Soap;

namespace SemanticKernelApp.Backend.Services;

/// <summary>
/// Default implementation of the task orchestrator.
/// Manages task execution, status tracking, and batch processing.
/// </summary>
public class DefaultTaskOrchestrator : ITaskOrchestrator
{
    private readonly ILogger<DefaultTaskOrchestrator> _logger;
    private readonly ConcurrentDictionary<string, TaskInfo> _tasks = new();
    private readonly ConcurrentDictionary<string, CancellationTokenSource> _cancellationTokens = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="DefaultTaskOrchestrator"/> class.
    /// </summary>
    public DefaultTaskOrchestrator(ILogger<DefaultTaskOrchestrator> logger)
    {
        _logger = logger;
    }

    /// <inheritdoc />
    public async Task<TaskExecutionResult> ExecuteAsync(
        string taskId,
        string taskType,
        string payload,
        int priority,
        int timeoutMs,
        string correlationId)
    {
        var taskInfo = new TaskInfo
        {
            TaskId = taskId,
            TaskType = taskType,
            Status = "Running",
            StartTime = DateTime.UtcNow,
            ProgressPercent = 0,
            CurrentStep = "Initializing"
        };

        _tasks[taskId] = taskInfo;
        var cts = new CancellationTokenSource(timeoutMs);
        _cancellationTokens[taskId] = cts;

        var agentTrace = new List<string> { "orchestrator" };

        try
        {
            // Simulate task processing through agents
            await ProcessTaskAsync(taskInfo, payload, cts.Token, agentTrace);

            taskInfo.Status = "Completed";
            taskInfo.ProgressPercent = 100;
            taskInfo.CurrentStep = "Done";

            _logger.LogInformation("Task {TaskId} completed successfully", taskId);

            return new TaskExecutionResult(
                ResultPayload: Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes($"{{\"taskId\":\"{taskId}\",\"result\":\"success\"}}")),
                AgentTrace: agentTrace);
        }
        catch (OperationCanceledException)
        {
            taskInfo.Status = "Cancelled";
            throw new TaskCanceledException($"Task {taskId} was cancelled");
        }
        catch (Exception ex)
        {
            taskInfo.Status = "Failed";
            taskInfo.CurrentStep = $"Error: {ex.Message}";
            throw;
        }
        finally
        {
            _cancellationTokens.TryRemove(taskId, out _);
        }
    }

    /// <inheritdoc />
    public Task<TaskStatusResult> GetStatusAsync(string taskId)
    {
        if (_tasks.TryGetValue(taskId, out var taskInfo))
        {
            return Task.FromResult(new TaskStatusResult(
                Status: taskInfo.Status,
                ProgressPercent: taskInfo.ProgressPercent,
                CurrentStep: taskInfo.CurrentStep,
                StartTime: taskInfo.StartTime,
                EstimatedCompletion: taskInfo.StartTime?.AddMinutes(5)));
        }

        return Task.FromResult(new TaskStatusResult(
            Status: "NotFound",
            ProgressPercent: 0,
            CurrentStep: null,
            StartTime: null,
            EstimatedCompletion: null));
    }

    /// <inheritdoc />
    public Task<bool> CancelAsync(string taskId, string? reason)
    {
        _logger.LogInformation("Cancelling task {TaskId}: {Reason}", taskId, reason);

        if (_cancellationTokens.TryGetValue(taskId, out var cts))
        {
            cts.Cancel();
            if (_tasks.TryGetValue(taskId, out var taskInfo))
            {
                taskInfo.Status = "Cancelled";
                taskInfo.CurrentStep = reason ?? "Cancelled by user";
            }
            return Task.FromResult(true);
        }

        return Task.FromResult(false);
    }

    /// <inheritdoc />
    public Task<IEnumerable<DependencyCheckResult>> CheckDependenciesAsync()
    {
        var results = new List<DependencyCheckResult>
        {
            new("database", true, 15),
            new("redis", true, 5),
            new("qdrant", true, 20),
            new("engine", true, 10),
            new("embeddings", true, 25)
        };

        return Task.FromResult<IEnumerable<DependencyCheckResult>>(results);
    }

    /// <inheritdoc />
    public async Task<int> SubmitBatchAsync(
        string batchId,
        IList<(string TaskId, string TaskType, string Payload, int Priority)> tasks,
        bool parallel,
        bool stopOnError)
    {
        _logger.LogInformation(
            "Processing batch {BatchId} with {TaskCount} tasks (parallel={Parallel})",
            batchId, tasks.Count, parallel);

        int acceptedCount = 0;

        if (parallel)
        {
            var parallelTasks = tasks.Select(async t =>
            {
                try
                {
                    await ExecuteAsync(t.TaskId, t.TaskType, t.Payload, t.Priority, 30000, batchId);
                    Interlocked.Increment(ref acceptedCount);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Batch task {TaskId} failed", t.TaskId);
                    if (stopOnError)
                    {
                        throw;
                    }
                }
            });

            try
            {
                await Task.WhenAll(parallelTasks);
            }
            catch when (!stopOnError)
            {
                // Continue processing even if some tasks failed
            }
        }
        else
        {
            foreach (var (taskId, taskType, payload, priority) in tasks)
            {
                try
                {
                    await ExecuteAsync(taskId, taskType, payload, priority, 30000, batchId);
                    acceptedCount++;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Batch task {TaskId} failed", taskId);
                    if (stopOnError)
                    {
                        break;
                    }
                }
            }
        }

        return acceptedCount;
    }

    private async Task ProcessTaskAsync(
        TaskInfo taskInfo,
        string payload,
        CancellationToken cancellationToken,
        List<string> agentTrace)
    {
        var steps = new[]
        {
            ("Validating input", "validator"),
            ("Processing with business rules", "business"),
            ("Executing semantic operations", "engine"),
            ("Storing results", "storage"),
            ("Finalizing", "orchestrator")
        };

        for (int i = 0; i < steps.Length; i++)
        {
            cancellationToken.ThrowIfCancellationRequested();

            var (step, agent) = steps[i];
            taskInfo.CurrentStep = step;
            taskInfo.ProgressPercent = (i + 1) * 100 / steps.Length;
            agentTrace.Add(agent);

            // Simulate processing time
            await Task.Delay(Random.Shared.Next(100, 500), cancellationToken);
        }
    }

    private class TaskInfo
    {
        public string TaskId { get; set; } = string.Empty;
        public string TaskType { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public DateTime? StartTime { get; set; }
        public int ProgressPercent { get; set; }
        public string? CurrentStep { get; set; }
    }
}
