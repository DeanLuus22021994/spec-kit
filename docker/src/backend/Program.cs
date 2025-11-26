// -----------------------------------------------------------------------
// <copyright file="Program.cs" company="SemanticKernelApp">
// Copyright (c) SemanticKernelApp. All rights reserved.
// </copyright>
// -----------------------------------------------------------------------

using System.Reflection;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;
using SemanticKernelApp.Backend.Services;
using SemanticKernelApp.Backend.Soap;
using SoapCore;

var builder = WebApplication.CreateBuilder(args);

// ============================================================================
// Service Registration
// ============================================================================

// Add controllers with JSON options
builder.Services.AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.CamelCase;
        options.JsonSerializerOptions.WriteIndented = true;
    });

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "Semantic Kernel Backend API",
        Version = "v1",
        Description = "Backend API for the Semantic Kernel Application with SOAP support"
    });
});

// ============================================================================
// SOAP Services Registration
// ============================================================================

builder.Services.AddSoapCore();
builder.Services.AddScoped<IOrchestratorSoapService, OrchestratorSoapServiceImpl>();
builder.Services.AddScoped<ITaskOrchestrator, DefaultTaskOrchestrator>();
builder.Services.AddScoped<IMetricsService, DefaultMetricsService>();

// ============================================================================
// OpenTelemetry Tracing
// ============================================================================

builder.Services.AddOpenTelemetry()
    .ConfigureResource(resource => resource
        .AddService(
            serviceName: "semantic-kernel-backend",
            serviceVersion: Assembly.GetExecutingAssembly().GetName().Version?.ToString() ?? "1.0.0"))
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddJaegerExporter(options =>
        {
            options.AgentHost = builder.Configuration["Jaeger:Host"] ?? "jaeger";
            options.AgentPort = int.Parse(builder.Configuration["Jaeger:Port"] ?? "6831");
        }));

// ============================================================================
// Health Checks
// ============================================================================

builder.Services.AddHealthChecks()
    .AddCheck("self", () => HealthCheckResult.Healthy("API is running"))
    .AddCheck<DatabaseHealthCheck>("database")
    .AddCheck<RedisHealthCheck>("redis")
    .AddCheck<VectorStoreHealthCheck>("vector-store");

// ============================================================================
// CORS Configuration
// ============================================================================

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins(
                "http://localhost:3000",
                "http://localhost:8080",
                "http://frontend:3000")
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials();
    });
});

// ============================================================================
// Kestrel Configuration
// ============================================================================

builder.WebHost.ConfigureKestrel(serverOptions =>
{
    serverOptions.ListenAnyIP(80);  // HTTP only in containers - TLS termination at nginx/gateway
});

// ============================================================================
// Logging Configuration
// ============================================================================

builder.Logging.ClearProviders();
builder.Logging.AddConsole();
builder.Logging.AddDebug();
builder.Logging.SetMinimumLevel(
    builder.Environment.IsDevelopment() ? LogLevel.Debug : LogLevel.Information);

var app = builder.Build();

// ============================================================================
// Middleware Pipeline
// ============================================================================

// Exception handling
app.UseExceptionHandler("/error");

// Development tools
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/swagger/v1/swagger.json", "Backend API v1");
        options.RoutePrefix = "swagger";
    });
}

// HTTPS redirection (disabled in containers)
if (!app.Environment.IsDevelopment())
{
    app.UseHttpsRedirection();
}

// CORS
app.UseCors("AllowFrontend");

// Routing & Authorization
app.UseRouting();
app.UseAuthorization();

// ============================================================================
// SOAP Endpoint Configuration
// ============================================================================

// SOAP endpoint for 3rd party integrations
((IEndpointRouteBuilder)app).UseSoapEndpoint<IOrchestratorSoapService>(
    "/soap/orchestrator.asmx",
    new SoapEncoderOptions(),
    SoapSerializer.DataContractSerializer);

// WSDL available at: /soap/orchestrator.asmx?wsdl

// ============================================================================
// REST API Endpoints
// ============================================================================

app.MapControllers();

// Health check endpoints
app.MapHealthChecks("/health", new HealthCheckOptions
{
    ResponseWriter = async (context, report) =>
    {
        context.Response.ContentType = "application/json";
        var result = System.Text.Json.JsonSerializer.Serialize(new
        {
            status = report.Status.ToString(),
            duration = report.TotalDuration.TotalMilliseconds,
            checks = report.Entries.Select(e => new
            {
                name = e.Key,
                status = e.Value.Status.ToString(),
                duration = e.Value.Duration.TotalMilliseconds,
                description = e.Value.Description
            })
        });
        await context.Response.WriteAsync(result);
    }
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
});

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = _ => false
});

// Error handler endpoint
app.Map("/error", (HttpContext context) =>
{
    return Results.Problem(
        title: "An error occurred",
        statusCode: 500);
});

// Root info endpoint
app.MapGet("/", () => new
{
    service = "Semantic Kernel Backend API",
    version = "1.0.0",
    endpoints = new
    {
        swagger = "/swagger",
        health = "/health",
        soap_wsdl = "/soap/orchestrator.asmx?wsdl",
        api = "/api"
    }
});

await app.RunAsync().ConfigureAwait(false);
