#include "AifredEngineClient.h"

#ifndef AIFRED_ENGINE_URL
#define AIFRED_ENGINE_URL "http://127.0.0.1:8787"
#endif

namespace aifred::services
{
namespace
{
struct HttpResult final
{
    int statusCode = 0;
    juce::String body;
};

HttpResult request(const juce::String& method,
                   const juce::String& path,
                   const juce::String& body,
                   const int timeoutMs)
{
    auto url = juce::URL(juce::String(AIFRED_ENGINE_URL) + path);
    if (body.isNotEmpty())
        url = url.withPOSTData(body);

    HttpResult result;
    const auto options = juce::URL::InputStreamOptions(juce::URL::ParameterHandling::inAddress)
        .withConnectionTimeoutMs(timeoutMs)
        .withNumRedirectsToFollow(0)
        .withStatusCode(&result.statusCode)
        .withHttpRequestCmd(method);
    if (body.isNotEmpty())
    {
        if (auto stream = url.createInputStream(
                options.withExtraHeaders("Content-Type: application/json\r\n")))
            result.body = stream->readEntireStreamAsString();
    }
    else if (auto stream = url.createInputStream(options))
    {
        result.body = stream->readEntireStreamAsString();
    }
    return result;
}

bool propertyBool(const juce::var& object, const char* name)
{
    const auto value = object.getProperty(name, {});
    return ! value.isVoid() && static_cast<bool>(value);
}
} // namespace

EngineHealth parseEngineHealth(const juce::String& json, const int httpStatusCode)
{
    EngineHealth result;
    if (httpStatusCode < 200 || httpStatusCode >= 300)
    {
        result.status = "AifredEngine unavailable.";
        return result;
    }

    const auto root = juce::JSON::parse(json);
    if (! root.isObject() || ! propertyBool(root, "engine_running"))
    {
        result.status = "AifredEngine health response invalid.";
        return result;
    }

    result.backendAvailable = true;
    result.provider = root.getProperty("provider", "").toString().trim().toStdString();
    result.model = root.getProperty("model_name", "").toString().trim().toStdString();
    result.providerAvailable = propertyBool(root, "ai_available")
        || propertyBool(root, "provider_ready")
        || propertyBool(root, "local_ai_ready");

    if (result.providerAvailable)
        result.status = result.provider.empty() ? "AI provider ready."
                                                : result.provider + " provider ready.";
    else
    {
        result.status = root.getProperty("last_error", "AI provider unavailable.")
                            .toString().trim().toStdString();
        if (result.status.empty())
            result.status = "AI provider unavailable.";
    }
    return result;
}

ChatResult parseChatResult(const juce::String& json, const int httpStatusCode)
{
    ChatResult result;
    const auto root = juce::JSON::parse(json);
    if (root.isObject())
    {
        result.response = root.getProperty("response", "").toString().trim().toStdString();
        result.error = root.getProperty("error", "").toString().trim().toStdString();
    }

    result.success = httpStatusCode >= 200 && httpStatusCode < 300
        && ! result.response.empty();
    if (! result.success && result.error.empty())
        result.error = httpStatusCode == 0 ? "AifredEngine is unavailable."
                                           : "AI provider did not return a usable response.";
    return result;
}

juce::String makeChatRequestJson(const juce::String& message,
                                 const juce::String& contextJson)
{
    auto context = juce::JSON::parse(contextJson);
    if (! context.isObject())
        context = juce::var(new juce::DynamicObject());

    auto root = std::make_unique<juce::DynamicObject>();
    root->setProperty("message", message);
    root->setProperty("context", context);
    return juce::JSON::toString(juce::var(root.release()), false);
}

AifredEngineClient& AifredEngineClient::instance()
{
    static AifredEngineClient client;
    return client;
}

bool AifredEngineClient::pingHealthAsync()
{
    bool expected = false;
    if (! healthInFlight_.compare_exchange_strong(expected, true))
        return false;

    healthWorker_ = std::jthread([this]
    {
        const auto http = request("GET", "/health", {}, 1500);
        auto next = parseEngineHealth(http.body, http.statusCode);
        {
            const std::scoped_lock lock(mutex_);
            next.revision = health_.revision + 1;
            health_ = std::move(next);
        }
        healthInFlight_.store(false);
    });
    return true;
}

bool AifredEngineClient::askAsync(juce::String message, juce::String contextJson)
{
    if (message.trim().isEmpty())
        return false;

    bool expected = false;
    if (! chatInFlight_.compare_exchange_strong(expected, true))
        return false;

    chatWorker_ = std::jthread([this, message = std::move(message), contextJson = std::move(contextJson)]
    {
        const auto body = makeChatRequestJson(message, contextJson);
        const auto http = request("POST", "/chat", body, 180000);
        auto next = parseChatResult(http.body, http.statusCode);
        {
            const std::scoped_lock lock(mutex_);
            next.revision = chat_.revision + 1;
            chat_ = std::move(next);
        }
        chatInFlight_.store(false);
    });
    return true;
}

EngineHealth AifredEngineClient::health() const
{
    const std::scoped_lock lock(mutex_);
    return health_;
}

ChatResult AifredEngineClient::lastChatResult() const
{
    const std::scoped_lock lock(mutex_);
    return chat_;
}

bool AifredEngineClient::healthInFlight() const noexcept
{
    return healthInFlight_.load();
}

bool AifredEngineClient::chatInFlight() const noexcept
{
    return chatInFlight_.load();
}
} // namespace aifred::services
