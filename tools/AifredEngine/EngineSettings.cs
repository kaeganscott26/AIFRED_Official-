using System.Text.Json;
using System.Text.Json.Nodes;

namespace Aifred.Engine;

public sealed record EngineSettings(
    string Provider,
    string Endpoint,
    string Model,
    string ApiKey,
    int TimeoutMs,
    int Port)
{
    public static EngineSettings Defaults => new(
        "ollama", "http://127.0.0.1:11434", "aifred:latest", "", 180_000, 8787);

    public static EngineSettings FromJson(JsonObject json, EngineSettings? fallback = null)
    {
        var current = fallback ?? Defaults;
        var provider = Text(json, "provider", Text(json, "provider_mode", current.Provider))
            .Trim().ToLowerInvariant();
        var endpoint = Text(json, "endpoint", Text(json, "custom_endpoint",
            Text(json, "ollama_url", current.Endpoint))).TrimEnd('/');
        var model = Text(json, "model", Text(json, "model_name", current.Model)).Trim();
        var apiKey = Text(json, "api_key", current.ApiKey).Trim();
        var timeout = Integer(json, "timeout_ms", current.TimeoutMs);
        var port = Integer(json, "port", current.Port);

        if (provider.Equals("ollama", StringComparison.OrdinalIgnoreCase) && string.IsNullOrWhiteSpace(endpoint))
            endpoint = Defaults.Endpoint;
        if (string.IsNullOrWhiteSpace(model))
            model = provider.Equals("ollama", StringComparison.OrdinalIgnoreCase)
                ? Defaults.Model : current.Model;
        if (provider is not ("ollama" or "openai" or "openai-compatible"))
            throw new InvalidOperationException("provider must be ollama, openai, or openai-compatible");
        if (!Uri.TryCreate(endpoint, UriKind.Absolute, out var uri)
            || (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps))
            throw new InvalidOperationException("provider endpoint must be an absolute HTTP or HTTPS URL");

        return new EngineSettings(provider, endpoint, model, apiKey,
            Math.Clamp(timeout, 1_000, 420_000), Math.Clamp(port, 1024, 65_535));
    }

    public EngineSettings WithEnvironmentOverrides()
    {
        var provider = Environment.GetEnvironmentVariable("AIFRED_PROVIDER")?.Trim();
        var endpoint = Environment.GetEnvironmentVariable("AIFRED_PROVIDER_ENDPOINT")?.Trim();
        var model = Environment.GetEnvironmentVariable("AIFRED_PROVIDER_MODEL")?.Trim();
        var apiKey = Environment.GetEnvironmentVariable("AIFRED_PROVIDER_API_KEY")?.Trim();
        return this with
        {
            Provider = string.IsNullOrWhiteSpace(provider) ? Provider : provider,
            Endpoint = string.IsNullOrWhiteSpace(endpoint) ? Endpoint : endpoint.TrimEnd('/'),
            Model = string.IsNullOrWhiteSpace(model) ? Model : model,
            ApiKey = string.IsNullOrWhiteSpace(apiKey) ? ApiKey : apiKey
        };
    }

    public JsonObject ToPersistedJson() => new()
    {
        ["provider"] = Provider,
        ["endpoint"] = Endpoint,
        ["model"] = Model,
        ["api_key"] = ApiKey,
        ["timeout_ms"] = TimeoutMs,
        ["port"] = Port
    };

    public JsonObject ToPublicJson() => new()
    {
        ["provider"] = Provider,
        ["endpoint"] = Endpoint,
        ["model"] = Model,
        ["api_key_configured"] = !string.IsNullOrWhiteSpace(ApiKey),
        ["timeout_ms"] = TimeoutMs,
        ["port"] = Port
    };

    static string Text(JsonObject json, string key, string fallback)
    {
        try { return json[key]?.GetValue<string>() ?? fallback; }
        catch { return fallback; }
    }

    static int Integer(JsonObject json, string key, int fallback)
    {
        try { return json[key]?.GetValue<int>() ?? fallback; }
        catch { return fallback; }
    }
}

public sealed class SettingsStore
{
    readonly string settingsPath;

    public SettingsStore(string? root = null)
    {
        var appData = root ?? Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        settingsPath = Path.Combine(appData, "Aifred", "Engine", "settings.json");
    }

    public EngineSettings Load()
    {
        if (!File.Exists(settingsPath))
        {
            Save(EngineSettings.Defaults);
            return EngineSettings.Defaults;
        }

        try
        {
            var json = JsonNode.Parse(File.ReadAllText(settingsPath))?.AsObject() ?? new JsonObject();
            return EngineSettings.FromJson(json);
        }
        catch
        {
            return EngineSettings.Defaults;
        }
    }

    public void Save(EngineSettings settings)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(settingsPath)!);
        File.WriteAllText(settingsPath,
            settings.ToPersistedJson().ToJsonString(new JsonSerializerOptions { WriteIndented = true }));
    }
}
