using System.Net;
using System.Text;
using System.Text.Json.Nodes;
using Aifred.Engine;

var tests = new EngineContractTests();
await tests.RunAsync();

sealed class EngineContractTests
{
    int failures;

    public async Task RunAsync()
    {
        await OllamaRoutePreservesQuestionAndContext();
        await OpenAiCompatibleRouteIsSelectable();
        await MissingProviderIsCleanlyUnavailable();
        PublicSettingsHideSecrets();
        if (failures != 0)
        {
            Console.Error.WriteLine($"AifredEngine contract tests: {failures} failure(s)");
            Environment.ExitCode = 1;
            return;
        }
        Console.WriteLine("AifredEngine contract tests: PASS");
    }

    async Task OllamaRoutePreservesQuestionAndContext()
    {
        var capture = new RequestCapture();
        var router = new ProviderRouter(() => new HttpClient(new MockHandler(capture, request =>
        {
            if (request.RequestUri?.AbsolutePath == "/api/tags")
                return Json(HttpStatusCode.OK, """{"models":[{"name":"aifred:latest"}]}""");
            return Json(HttpStatusCode.OK,
                """{"message":{"role":"assistant","content":"A natural mocked reply."}}""");
        })));
        var settings = EngineSettings.Defaults with { TimeoutMs = 5000 };
        var health = await router.CheckAsync(settings);
        Expect(health.Available, "mocked Ollama health must be available");

        const string question = "Why does my chorus feel wider but weaker?";
        var context = JsonNode.Parse("""{"mode":"Analyze","current":{"metrics":{"width":{"available":true,"value":0.72}}}}""")!.AsObject();
        var reply = await router.ChatAsync(settings, question, context);
        Expect(reply.Success && reply.Response == "A natural mocked reply.",
            "mocked Ollama response must pass through");
        var outbound = JsonNode.Parse(capture.LastBody)!.AsObject();
        var userContent = outbound["messages"]?[1]?["content"]?.GetValue<string>() ?? "";
        var userPayload = JsonNode.Parse(userContent)!.AsObject();
        Expect(userPayload["message"]?.GetValue<string>() == question,
            "arbitrary user question must be passed through unchanged");
        Expect(userPayload["context"]?["mode"]?.GetValue<string>() == "Analyze",
            "authoritative context must accompany the question");
    }

    async Task OpenAiCompatibleRouteIsSelectable()
    {
        var capture = new RequestCapture();
        var router = new ProviderRouter(() => new HttpClient(new MockHandler(capture, request =>
        {
            if (request.RequestUri?.AbsolutePath == "/v1/models")
                return Json(HttpStatusCode.OK, """{"data":[{"id":"mix-model"}]}""");
            return Json(HttpStatusCode.OK,
                """{"choices":[{"message":{"content":"Compatible mocked reply."}}]}""");
        })));
        var settings = new EngineSettings("openai-compatible", "https://provider.invalid/v1",
            "mix-model", "test-only-key", 5000, 8787);
        var health = await router.CheckAsync(settings);
        Expect(health.Available, "mocked OpenAI-compatible health must be available");
        var reply = await router.ChatAsync(settings, "What changed?",
            JsonNode.Parse("""{"mode":"Compare","mix_a":{},"mix_b":{},"delta":{}}""")!.AsObject());
        Expect(reply.Success && reply.Response == "Compatible mocked reply.",
            "OpenAI-compatible route must return provider text");
        Expect(capture.SawBearerToken, "OpenAI-compatible request must use configured bearer token");
    }

    async Task MissingProviderIsCleanlyUnavailable()
    {
        var router = new ProviderRouter(() => new HttpClient(new MockHandler(new(), _ =>
            throw new HttpRequestException("offline"))));
        var settings = new EngineSettings("openai-compatible", "https://provider.invalid/v1",
            "mix-model", "", 1000, 8787);
        var health = await router.CheckAsync(settings);
        Expect(!health.Available && health.Error?.Contains("no configured API key") == true,
            "missing provider credentials must produce a clean unavailable state");
        var reply = await router.ChatAsync(settings, "Still meter?", new JsonObject());
        Expect(!reply.Success && reply.Error?.Contains("no configured API key") == true,
            "chat must remain unavailable without pretending the engine or DSP failed");
    }

    void PublicSettingsHideSecrets()
    {
        var settings = EngineSettings.Defaults with { ApiKey = "do-not-return" };
        var json = settings.ToPublicJson().ToJsonString();
        Expect(!json.Contains("do-not-return") && !json.Contains("\"api_key\""),
            "public settings payload must not expose provider secrets");
    }

    void Expect(bool condition, string message)
    {
        if (condition) return;
        failures++;
        Console.Error.WriteLine("FAIL: " + message);
    }

    static HttpResponseMessage Json(HttpStatusCode status, string json) => new(status)
    {
        Content = new StringContent(json, Encoding.UTF8, "application/json")
    };
}

sealed class RequestCapture
{
    public string LastBody { get; set; } = "";
    public bool SawBearerToken { get; set; }
}

sealed class MockHandler(RequestCapture capture,
                         Func<HttpRequestMessage, HttpResponseMessage> responseFactory)
    : HttpMessageHandler
{
    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request,
                                                                  CancellationToken cancellationToken)
    {
        capture.SawBearerToken |= request.Headers.Authorization?.Scheme == "Bearer";
        if (request.Content != null)
            capture.LastBody = await request.Content.ReadAsStringAsync(cancellationToken);
        return responseFactory(request);
    }
}
