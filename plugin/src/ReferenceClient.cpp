#include "ReferenceClient.h"

#include <algorithm>
#include <cmath>
#ifndef AIFRED_REFERENCE_API_URL
#define AIFRED_REFERENCE_API_URL "https://www.north3rnlight3r.com/api/v1/references"
#endif

namespace aifred::services
{
namespace
{
constexpr auto expectedContract = "aifred.references.v1";

analysis::MetricValue parseMetricValue(const juce::var& field)
{
    if (! field.isObject() || ! static_cast<bool>(field.getProperty("available", false)))
        return {};

    const auto value = field.getProperty("value", {});
    if (! value.isDouble() && ! value.isInt() && ! value.isInt64())
        return {};

    const auto numeric = static_cast<double>(value);
    return std::isfinite(numeric) ? analysis::MetricValue { numeric, true }
                                  : analysis::MetricValue {};
}

analysis::MetricValue parseMetric(const juce::var& metrics, const char* name)
{
    return parseMetricValue(metrics.getProperty(name, {}));
}

ReferenceProfile parseReference(const juce::var& value)
{
    ReferenceProfile result;
    if (! value.isObject() || ! static_cast<bool>(value.getProperty("available", false)))
        return result;

    result.id = value.getProperty("id", "").toString().trim().toStdString();
    auto name = value.getProperty("name", "").toString().trim();
    if (name.containsChar('\\') || name.startsWithChar('/')
        || (name.length() > 1 && name[1] == ':'))
        name = juce::File(name).getFileName();
    result.name = name.toStdString();
    result.version = value.getProperty("version", "").toString().trim().toStdString();
    if (result.id.empty() || result.name.empty())
        return {};

    const auto metrics = value.getProperty("metrics", {});
    result.metrics.samplePeakDbfs = parseMetric(metrics, "sample_peak_dbfs");
    result.metrics.truePeakDbtp = parseMetric(metrics, "true_peak_dbtp");
    result.metrics.rmsDbfs = parseMetric(metrics, "rms_dbfs");
    result.metrics.crestDb = parseMetric(metrics, "crest_db");
    result.metrics.momentaryLufs = parseMetric(metrics, "momentary_lufs");
    result.metrics.shortTermLufs = parseMetric(metrics, "short_term_lufs");
    result.metrics.integratedLufs = parseMetric(metrics, "integrated_lufs");
    result.metrics.loudnessRangeLu = parseMetric(metrics, "lra_lu");
    result.metrics.stereoWidth = parseMetric(metrics, "stereo_width");
    result.metrics.correlation = parseMetric(metrics, "correlation");
    result.metrics.punchDb = parseMetric(metrics, "punch_db");
    result.metrics.spectralTiltDbPerOctave = parseMetric(metrics, "spectral_tilt_db_per_octave");

    const auto spectrum = metrics.getProperty("spectrum_band_dbfs", {});
    if (const auto* values = spectrum.getArray())
    {
        const auto count = std::min<int>(values->size(),
                                         static_cast<int>(result.metrics.legacySpectrumBandDbfs.size()));
        for (int index = 0; index < count; ++index)
            result.metrics.legacySpectrumBandDbfs[static_cast<std::size_t>(index)] =
                parseMetricValue(values->getReference(index));
    }

    result.available = true;
    return result;
}
} // namespace

ReferenceCatalog parseReferenceCatalog(const juce::String& json)
{
    ReferenceCatalog result;
    const auto root = juce::JSON::parse(json);
    if (! root.isObject())
    {
        result.status = ReferenceCatalogStatus::error;
        result.message = "Reference service returned invalid JSON.";
        return result;
    }

    result.contractVersion = root.getProperty("contract_version", "").toString().toStdString();
    if (result.contractVersion != expectedContract)
    {
        result.status = ReferenceCatalogStatus::error;
        result.message = "Reference service contract is unsupported.";
        return result;
    }

    if (const auto* references = root.getProperty("references", {}).getArray())
    {
        result.references.reserve(static_cast<std::size_t>(references->size()));
        for (const auto& item : *references)
        {
            auto parsed = parseReference(item);
            if (parsed.available)
                result.references.push_back(std::move(parsed));
        }
    }

    if (result.references.empty())
    {
        auto current = parseReference(root.getProperty("reference", {}));
        if (current.available)
            result.references.push_back(std::move(current));
    }

    if (! result.references.empty())
    {
        result.status = ReferenceCatalogStatus::available;
        result.message = std::to_string(result.references.size()) + " references available.";
    }
    else
    {
        result.status = ReferenceCatalogStatus::unavailable;
        result.message = root.getProperty("reason", "No usable references are available.")
                             .toString().toStdString();
    }
    return result;
}

analysis::ViewSnapshot referenceAsComparableSnapshot(
    const ReferenceProfile& reference) noexcept
{
    analysis::ViewSnapshot snapshot;
    if (! reference.available)
        return snapshot;

    // Only definitions shared exactly with the live 4.0 snapshot are mapped.
    // Integrated loudness and the legacy nine-band spectrum are deliberately
    // left out rather than relabelled as short-term LUFS or full FFT bins.
    snapshot.samplePeakDbfs = reference.metrics.samplePeakDbfs;
    snapshot.rmsDbfs = reference.metrics.rmsDbfs;
    snapshot.crestDb = reference.metrics.crestDb;
    snapshot.shortTermLufs = reference.metrics.shortTermLufs;
    snapshot.width = reference.metrics.stereoWidth;
    snapshot.correlation = reference.metrics.correlation;
    return snapshot;
}

ReferenceClient& ReferenceClient::instance()
{
    static ReferenceClient client;
    return client;
}

bool ReferenceClient::refreshAsync()
{
    bool expected = false;
    if (! requestInFlight_.compare_exchange_strong(expected, true))
        return false;

    {
        const std::scoped_lock lock(mutex_);
        state_.status = ReferenceCatalogStatus::loading;
        state_.contractVersion.clear();
        state_.message = "Loading production references...";
        state_.references.clear();
        ++state_.revision;
    }

    worker_ = std::jthread([this]
    {
        int statusCode = 0;
        const juce::URL url(AIFRED_REFERENCE_API_URL);
        const auto options = juce::URL::InputStreamOptions(
            juce::URL::ParameterHandling::inAddress)
            .withConnectionTimeoutMs(5000)
            .withNumRedirectsToFollow(2)
            .withStatusCode(&statusCode);

        ReferenceCatalog next;
        if (auto stream = url.createInputStream(options))
        {
            const auto body = stream->readEntireStreamAsString();
            next = parseReferenceCatalog(body);
            if (statusCode < 200 || statusCode >= 300)
            {
                next = {};
                next.status = ReferenceCatalogStatus::error;
                next.message = "Reference service request failed.";
            }
        }
        else
        {
            next.status = ReferenceCatalogStatus::error;
            next.message = "Reference service is unavailable.";
        }

        {
            const std::scoped_lock lock(mutex_);
            next.revision = state_.revision + 1;
            state_ = std::move(next);
        }
        requestInFlight_.store(false);
    });
    return true;
}

ReferenceCatalog ReferenceClient::state() const
{
    const std::scoped_lock lock(mutex_);
    return state_;
}

bool ReferenceClient::requestInFlight() const noexcept
{
    return requestInFlight_.load();
}
} // namespace aifred::services
