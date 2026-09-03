using System.Net;
using System.Text;
using System.Text.Json.Nodes;
using Aifred.Engine;

var runtime = new AifredRuntime();
await runtime.RunAsync();

sealed class AifredRuntime
{
    const string EngineVersion = "1.1.0";
    readonly HttpListener listener = new();
    readonly SettingsStore settingsStore = new();
    readonly ProviderRouter providerRouter = new();
    readonly string logPath;
    EngineSettings settings;

    public AifredRuntime()
    {
        settings = settingsStore.Load();
        var appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        logPath = Path.Combine(appData, "Aifred", "Engine", "engine.log");
    }

    public async Task RunAsync()
    {
        listener.Prefixes.Add($"http://127.0.0.1:{settings.Port}/");
        listener.Start();
        Log($"AifredEngine {EngineVersion} started on loopback port {settings.Port}");
        while (listener.IsListening)
        {
            try
            {
                var context = await listener.GetContextAsync();
                _ = Task.Run(() => HandleAsync(context));
            }
            catch (Exception exception) when (exception is HttpListenerException
                                               or ObjectDisposedException)
            {
                break;
            }
        }
    }

    async Task HandleAsync(HttpListenerContext context)
    {
        try
        {
            var path = context.Request.Url?.AbsolutePath.TrimEnd('/').ToLowerInvariant() ?? "";
            if (context.Request.HttpMethod == "GET" && path == "/health")
            {
                var effective = settings.WithEnvironmentOverrides();
                using var healthTimeout = new CancellationTokenSource(
                    TimeSpan.FromMilliseconds(Math.Min(3_000, effective.TimeoutMs)));
                var provider = await providerRouter.CheckAsync(effective, healthTimeout.Token);
                await WriteJsonAsync(context, new JsonObject
                {
                    ["ok"] = true,
                    ["engine_running"] = true,
                    ["engine_version"] = EngineVersion,
                    ["provider"] = provider.Provider,
                    ["model_name"] = provider.Model,
                    ["provider_ready"] = provider.Available,
                    ["ai_available"] = provider.Available,
                    ["local_ai_ready"] = provider.Available
                        && provider.Provider.Equals("ollama", StringComparison.OrdinalIgnoreCase),
                    ["last_error"] = provider.Error
                });
            }
            else if (context.Request.HttpMethod == "POST" && path == "/chat")
            {
                var body = await ReadJsonAsync(context.Request);
                var message = body["message"]?.GetValue<string>() ?? "";
                var suppliedContext = body["context"] as JsonObject ?? new JsonObject();
                var reply = await providerRouter.ChatAsync(
                    settings.WithEnvironmentOverrides(), message, suppliedContext);
                await WriteJsonAsync(context, reply.Success
                    ? new JsonObject { ["ok"] = true, ["response"] = reply.Response }
                    : new JsonObject { ["ok"] = false, ["error"] = reply.Error },
                    reply.Success ? 200 : 503);
            }
            else if (context.Request.HttpMethod == "GET" && path == "/v1/settings")
            {
                await WriteJsonAsync(context,
                    new JsonObject { ["ok"] = true, ["settings"] = settings.ToPublicJson() });
            }
            else if (context.Request.HttpMethod == "POST" && path == "/v1/settings")
            {
                settings = EngineSettings.FromJson(await ReadJsonAsync(context.Request), settings);
                settingsStore.Save(settings);
                await WriteJsonAsync(context,
                    new JsonObject { ["ok"] = true, ["settings"] = settings.ToPublicJson() });
            }
            else if (context.Request.HttpMethod == "POST" && path == "/v1/restart")
            {
                await WriteJsonAsync(context,
                    new JsonObject { ["ok"] = true, ["message"] = "shutdown accepted; relaunch required" });
                _ = Task.Run(async () => { await Task.Delay(100); Environment.Exit(0); });
            }
            else
            {
                await WriteJsonAsync(context,
                    new JsonObject { ["ok"] = false, ["error"] = "unknown route" }, 404);
            }
        }
        catch (Exception exception)
        {
            Log("request failed: " + exception.GetType().Name);
            if (context.Response.OutputStream.CanWrite)
                await WriteJsonAsync(context,
                    new JsonObject { ["ok"] = false, ["error"] = "engine request failed" }, 500);
        }
    }

    static async Task<JsonObject> ReadJsonAsync(HttpListenerRequest request)
    {
        using var reader = new StreamReader(request.InputStream, request.ContentEncoding);
        var text = await reader.ReadToEndAsync();
        return string.IsNullOrWhiteSpace(text)
            ? new JsonObject() : JsonNode.Parse(text)?.AsObject() ?? new JsonObject();
    }

    static async Task WriteJsonAsync(HttpListenerContext context, JsonObject body, int status = 200)
    {
        var bytes = Encoding.UTF8.GetBytes(body.ToJsonString());
        context.Response.StatusCode = status;
        context.Response.ContentType = "application/json; charset=utf-8";
        context.Response.ContentLength64 = bytes.Length;
        context.Response.Headers["Cache-Control"] = "no-store";
        await context.Response.OutputStream.WriteAsync(bytes);
        context.Response.Close();
    }

    void Log(string message)
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(logPath)!);
            File.AppendAllText(logPath, $"[{DateTimeOffset.Now:O}] {message}{Environment.NewLine}");
        }
        catch { }
    }
}
