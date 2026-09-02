#pragma once

#include <functional>
#include <optional>
#include <string>

namespace aifred::update
{
// Update work is message/background-thread only. This interface must never be
// called by processBlock or any realtime analysis component.
struct UpdateManifest final
{
    std::string version;
    std::string channel;
    std::string downloadUrl;
    std::string sha256;
    std::string minimumUpdaterVersion;
};

enum class UpdateCheckStatus
{
    upToDate,
    updateAvailable,
    unavailable,
    invalidManifest
};

struct UpdateCheckResult final
{
    UpdateCheckStatus status = UpdateCheckStatus::unavailable;
    std::optional<UpdateManifest> manifest;
    std::string detail;
};

class UpdateCheckSource
{
public:
    using Completion = std::function<void(UpdateCheckResult)>;

    virtual ~UpdateCheckSource() = default;
    virtual void checkForUpdate(std::string currentVersion,
                                std::string channel,
                                Completion completion) = 0;
};

class ExternalUpdater
{
public:
    virtual ~ExternalUpdater() = default;

    // The updater owns download/hash verification and replacement only after
    // the user has closed every DAW process that may have the VST3 loaded.
    virtual bool stage(const UpdateManifest& manifest, std::string& error) = 0;
    virtual bool launchAfterHostExit(std::string& error) = 0;
};
} // namespace aifred::update
