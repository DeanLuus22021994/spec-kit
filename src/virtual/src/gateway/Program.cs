// -----------------------------------------------------------------------
// <copyright file="Program.cs" company="SemanticKernelApp">
// Copyright (c) SemanticKernelApp. All rights reserved.
// </copyright>
// -----------------------------------------------------------------------

using Microsoft.Extensions.Logging;

var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddHealthChecks();
builder.Services.AddHttpClient();

// Configure Kestrel
builder.WebHost.ConfigureKestrel(serverOptions =>
{
    serverOptions.ListenAnyIP(80);
});

// Add logging
builder.Logging.ClearProviders();
builder.Logging.AddConsole();

var app = builder.Build();

var logger = app.Services.GetRequiredService<ILogger<Program>>();

// API Gateway routing
app.MapGet("/", () => "API Gateway - Semantic Kernel App");
app.MapHealthChecks("/health");

// Proxy routes to backend services
app.Map("/api/backend/{**path}", async (HttpContext context) =>
{
    var backend = Environment.GetEnvironmentVariable("BACKEND_URL") ?? "http://backend:80";
    var path = context.Request.RouteValues["path"]?.ToString() ?? string.Empty;

    logger.LogInformation("Redirecting to backend: {Backend}/{Path}", backend, path);
    context.Response.Redirect($"{backend}/{path}");

    await Task.CompletedTask.ConfigureAwait(false);
});

app.Map("/api/engine/{**path}", async (HttpContext context) =>
{
    var engine = Environment.GetEnvironmentVariable("ENGINE_URL") ?? "http://engine:80";
    var path = context.Request.RouteValues["path"]?.ToString() ?? string.Empty;

    logger.LogInformation("Redirecting to engine: {Engine}/{Path}", engine, path);
    context.Response.Redirect($"{engine}/{path}");

    await Task.CompletedTask.ConfigureAwait(false);
});

await app.RunAsync().ConfigureAwait(false);

/// <summary>
/// Program entry point marker class for logging.
/// </summary>
public partial class Program
{
}
