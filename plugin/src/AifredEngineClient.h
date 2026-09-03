#pragma once

#include <juce_core/juce_core.h>

#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <thread>

namespace aifred::services
{
struct EngineHealth final
{
    bool backendAvailable = false;
    bool providerAvailable = false;
    std::string provider;
    std::string model;
    std::string status;
    std::uint64_t revision = 0;
};

struct ChatResult final
{
    bool success = false;
    std::string response;
    std::string error;
    std::uint64_t revision = 0;
};

[[nodiscard]] EngineHealth parseEngineHealth(const juce::String& json,
                                             int httpStatusCode);
[[nodiscard]] ChatResult parseChatResult(const juce::String& json,
                                         int httpStatusCode);
[[nodiscard]] juce::String makeChatRequestJson(const juce::String& message,
                                               const juce::String& contextJson);

class AifredEngineClient final
{
public:
    static AifredEngineClient& instance();

    bool pingHealthAsync();
    bool askAsync(juce::String message, juce::String contextJson);
    [[nodiscard]] EngineHealth health() const;
    [[nodiscard]] ChatResult lastChatResult() const;
    [[nodiscard]] bool healthInFlight() const noexcept;
    [[nodiscard]] bool chatInFlight() const noexcept;

private:
    AifredEngineClient() = default;

    mutable std::mutex mutex_;
    EngineHealth health_;
    ChatResult chat_;
    std::atomic<bool> healthInFlight_ { false };
    std::atomic<bool> chatInFlight_ { false };
    std::jthread healthWorker_;
    std::jthread chatWorker_;
};
} // namespace aifred::services
