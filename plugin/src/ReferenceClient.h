#pragma once

#include <juce_core/juce_core.h>

#include "core/analysis/AnalysisSnapshot.h"

#include <array>
#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

namespace aifred::services
{
struct ReferenceMetrics final
{
    static constexpr std::size_t legacySpectrumBandCount = 9;
    static constexpr std::array<double, legacySpectrumBandCount> legacySpectrumCentresHz {
        40.0, 80.0, 160.0, 315.0, 630.0, 1250.0, 2500.0, 5000.0, 8000.0
    };

    analysis::MetricValue samplePeakDbfs;
    analysis::MetricValue truePeakDbtp;
    analysis::MetricValue rmsDbfs;
    analysis::MetricValue crestDb;
    analysis::MetricValue momentaryLufs;
    analysis::MetricValue shortTermLufs;
    analysis::MetricValue integratedLufs;
    analysis::MetricValue loudnessRangeLu;
    analysis::MetricValue stereoWidth;
    analysis::MetricValue correlation;
    analysis::MetricValue punchDb;
    analysis::MetricValue spectralTiltDbPerOctave;
    std::array<analysis::MetricValue, legacySpectrumBandCount> legacySpectrumBandDbfs {};
};

struct ReferenceProfile final
{
    bool available = false;
    std::string id;
    std::string name;
    std::string version;
    ReferenceMetrics metrics;
};

enum class ReferenceCatalogStatus
{
    idle,
    loading,
    available,
    unavailable,
    error
};

struct ReferenceCatalog final
{
    ReferenceCatalogStatus status = ReferenceCatalogStatus::idle;
    std::string contractVersion;
    std::string message;
    std::vector<ReferenceProfile> references;
    std::uint64_t revision = 0;
};

[[nodiscard]] ReferenceCatalog parseReferenceCatalog(const juce::String& json);
[[nodiscard]] analysis::AnalysisSnapshot referenceAsComparableSnapshot(
    const ReferenceProfile& reference) noexcept;

class ReferenceClient final
{
public:
    static ReferenceClient& instance();

    bool refreshAsync();
    [[nodiscard]] ReferenceCatalog state() const;
    [[nodiscard]] bool requestInFlight() const noexcept;

private:
    ReferenceClient() = default;

    mutable std::mutex mutex_;
    ReferenceCatalog state_;
    std::atomic<bool> requestInFlight_ { false };
    std::jthread worker_;
};
} // namespace aifred::services
