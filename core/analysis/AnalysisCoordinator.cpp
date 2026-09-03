#include "AnalysisCoordinator.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <type_traits>

namespace aifred::analysis
{
namespace
{
constexpr std::size_t peakIndex = 0;
constexpr std::size_t rmsIndex = 1;
constexpr std::size_t crestIndex = 2;
constexpr std::size_t loudnessIndex = 3;
constexpr std::size_t widthIndex = 4;
constexpr std::size_t correlationIndex = 5;
constexpr std::size_t maxSampleOverIndex = 6;

static_assert(sizeof(double) == sizeof(std::uint64_t));
static_assert(std::atomic<std::uint64_t>::is_always_lock_free,
              "AIFRED snapshots require lock-free 64-bit atomics.");
static_assert(AnalysisSnapshot::spectrumFftSize == dsp::SpectrumResult::fftSize);
static_assert(AnalysisSnapshot::spectrumBinCount == dsp::SpectrumResult::binCount);
static_assert(AnalysisSnapshot::spectrumBandCount == dsp::SpectrumResult::bandCount);
}

AnalysisCoordinator::AtomicSnapshotStorage::AtomicSnapshotStorage() noexcept
{
    for (auto& value : metricValues_)
        value.store(0, std::memory_order_relaxed);
    for (auto& valid : metricValidity_)
        valid.store(0, std::memory_order_relaxed);
    for (auto& value : binValues_)
        value.store(0, std::memory_order_relaxed);
    for (auto& valid : binValidity_)
        valid.store(0, std::memory_order_relaxed);
    for (auto& value : bandValues_)
        value.store(0, std::memory_order_relaxed);
    for (auto& valid : bandValidity_)
        valid.store(0, std::memory_order_relaxed);
}

std::uint64_t AnalysisCoordinator::AtomicSnapshotStorage::encodeDouble(
    const double value) noexcept
{
    std::uint64_t encoded = 0;
    std::memcpy(&encoded, &value, sizeof(encoded));
    return encoded;
}

double AnalysisCoordinator::AtomicSnapshotStorage::decodeDouble(
    const std::uint64_t value) noexcept
{
    double decoded = 0.0;
    std::memcpy(&decoded, &value, sizeof(decoded));
    return decoded;
}

void AnalysisCoordinator::AtomicSnapshotStorage::storeMetric(
    std::atomic<std::uint64_t>& value,
    std::atomic<std::uint64_t>& valid,
    const MetricValue& metric) noexcept
{
    value.store(encodeDouble(metric.value), std::memory_order_relaxed);
    valid.store(metric.valid ? 1U : 0U, std::memory_order_relaxed);
}

MetricValue AnalysisCoordinator::AtomicSnapshotStorage::loadMetric(
    const std::atomic<std::uint64_t>& value,
    const std::atomic<std::uint64_t>& valid) noexcept
{
    return { decodeDouble(value.load(std::memory_order_relaxed)),
             valid.load(std::memory_order_relaxed) != 0U };
}

void AnalysisCoordinator::AtomicSnapshotStorage::publish(
    const AnalysisSnapshot& snapshot) noexcept
{
    // Single audio-thread writer seqlock. Payload members are atomic too, so
    // retrying readers are coherent without creating C++ data races.
    const auto oddGuard = guard_.load(std::memory_order_relaxed) + 1U;
    guard_.store(oddGuard, std::memory_order_release);

    sequence_.store(snapshot.sequence, std::memory_order_relaxed);
    audioSampleClock_.store(snapshot.audioSampleClock, std::memory_order_relaxed);
    elapsedSeconds_.store(encodeDouble(snapshot.elapsedSeconds), std::memory_order_relaxed);
    hasSignal_.store(snapshot.hasSignal ? 1U : 0U, std::memory_order_relaxed);
    sampleClipActive_.store(snapshot.sampleClipActive ? 1U : 0U, std::memory_order_relaxed);
    sampleClipCount_.store(snapshot.sampleClipCount, std::memory_order_relaxed);
    storeMetric(metricValues_[peakIndex], metricValidity_[peakIndex], snapshot.samplePeakDbfs);
    storeMetric(metricValues_[rmsIndex], metricValidity_[rmsIndex], snapshot.rmsDbfs);
    storeMetric(metricValues_[crestIndex], metricValidity_[crestIndex], snapshot.crestDb);
    storeMetric(metricValues_[loudnessIndex], metricValidity_[loudnessIndex], snapshot.shortTermLufs);
    storeMetric(metricValues_[widthIndex], metricValidity_[widthIndex], snapshot.width);
    storeMetric(metricValues_[correlationIndex], metricValidity_[correlationIndex], snapshot.correlation);
    storeMetric(metricValues_[maxSampleOverIndex], metricValidity_[maxSampleOverIndex], snapshot.maxSampleOverDb);
    storeMetric(spectrumBinWidthValue_, spectrumBinWidthValidity_, snapshot.spectrumBinWidthHz);
    for (std::size_t bin = 0; bin < snapshot.spectrumBins.size(); ++bin)
        storeMetric(binValues_[bin], binValidity_[bin], snapshot.spectrumBins[bin]);
    for (std::size_t band = 0; band < snapshot.spectrumBands.size(); ++band)
        storeMetric(bandValues_[band], bandValidity_[band], snapshot.spectrumBands[band]);

    guard_.store(oddGuard + 1U, std::memory_order_release);
}

AnalysisSnapshot AnalysisCoordinator::AtomicSnapshotStorage::load() const noexcept
{
    AnalysisSnapshot snapshot;
    for (;;)
    {
        const auto before = guard_.load(std::memory_order_acquire);
        if ((before & 1U) != 0U)
            continue;

        snapshot.sequence = sequence_.load(std::memory_order_relaxed);
        snapshot.audioSampleClock = audioSampleClock_.load(std::memory_order_relaxed);
        snapshot.elapsedSeconds = decodeDouble(elapsedSeconds_.load(std::memory_order_relaxed));
        snapshot.hasSignal = hasSignal_.load(std::memory_order_relaxed) != 0U;
        snapshot.sampleClipActive = sampleClipActive_.load(std::memory_order_relaxed) != 0U;
        snapshot.sampleClipCount = sampleClipCount_.load(std::memory_order_relaxed);
        snapshot.samplePeakDbfs = loadMetric(metricValues_[peakIndex], metricValidity_[peakIndex]);
        snapshot.rmsDbfs = loadMetric(metricValues_[rmsIndex], metricValidity_[rmsIndex]);
        snapshot.crestDb = loadMetric(metricValues_[crestIndex], metricValidity_[crestIndex]);
        snapshot.shortTermLufs = loadMetric(metricValues_[loudnessIndex], metricValidity_[loudnessIndex]);
        snapshot.width = loadMetric(metricValues_[widthIndex], metricValidity_[widthIndex]);
        snapshot.correlation = loadMetric(metricValues_[correlationIndex], metricValidity_[correlationIndex]);
        snapshot.maxSampleOverDb = loadMetric(metricValues_[maxSampleOverIndex], metricValidity_[maxSampleOverIndex]);
        snapshot.spectrumBinWidthHz = loadMetric(spectrumBinWidthValue_, spectrumBinWidthValidity_);
        for (std::size_t bin = 0; bin < snapshot.spectrumBins.size(); ++bin)
            snapshot.spectrumBins[bin] = loadMetric(binValues_[bin], binValidity_[bin]);
        for (std::size_t band = 0; band < snapshot.spectrumBands.size(); ++band)
            snapshot.spectrumBands[band] = loadMetric(bandValues_[band], bandValidity_[band]);

        const auto after = guard_.load(std::memory_order_acquire);
        if (before == after)
            return snapshot;
    }
}

AnalysisCoordinator::AnalysisCoordinator() noexcept = default;

void AnalysisCoordinator::prepare(const double sampleRate,
                                  const int maxBlockSize,
                                  const int numChannels)
{
    (void) maxBlockSize;
    sampleRate_ = std::max(8000.0, sampleRate);
    signalHoldFrames_ = static_cast<std::uint64_t>(
        std::max(1.0, std::round(sampleRate_ * signalHoldSeconds)));
    levelAnalyzer_.prepare(sampleRate_);
    loudnessAnalyzer_.prepare(sampleRate_, numChannels);
    stereoAnalyzer_.prepare(sampleRate_);
    spectrumAnalyzer_.prepare(sampleRate_);
    resetRequested_.store(false, std::memory_order_release);
    prepared_ = true;
    resetOnAudioThread();
}

void AnalysisCoordinator::reset() noexcept
{
    // The GUI/message thread never mutates analyzer state. While pending,
    // getSnapshot() exposes an immediately cleared state; process() performs
    // the actual reset before accepting more audio.
    resetRequested_.store(true, std::memory_order_release);
}

void AnalysisCoordinator::resetOnAudioThread() noexcept
{
    levelAnalyzer_.reset();
    loudnessAnalyzer_.reset();
    stereoAnalyzer_.reset();
    spectrumAnalyzer_.reset();
    spectrumResult_ = {};
    currentSnapshot_ = {};
    signalHoldRemainingFrames_ = 0;
    publishedSnapshot_.publish(currentSnapshot_);
}

bool AnalysisCoordinator::bufferHasSignal(const float* const* channels,
                                          const int numChannels,
                                          const int numSamples) const noexcept
{
    if (channels == nullptr || numChannels <= 0 || numSamples <= 0)
        return false;

    for (int channel = 0; channel < numChannels; ++channel)
    {
        if (channels[channel] == nullptr)
            continue;
        for (int frame = 0; frame < numSamples; ++frame)
        {
            const auto sample = channels[channel][frame];
            if (std::isfinite(sample) && std::abs(sample) >= signalFloorLinear)
                return true;
        }
    }
    return false;
}

void AnalysisCoordinator::updateClipState(const float* const* channels,
                                          const int numChannels,
                                          const int numSamples) noexcept
{
    double maximumMagnitude = 0.0;
    std::uint64_t clippedSamples = 0;
    for (int channel = 0; channel < numChannels; ++channel)
    {
        const auto* samples = channels[channel];
        if (samples == nullptr)
            continue;
        for (int frame = 0; frame < numSamples; ++frame)
        {
            const auto magnitude = std::abs(static_cast<double>(samples[frame]));
            if (std::isfinite(magnitude) && magnitude >= 1.0)
            {
                ++clippedSamples;
                maximumMagnitude = std::max(maximumMagnitude, magnitude);
            }
        }
    }

    if (clippedSamples == 0)
        return;

    currentSnapshot_.sampleClipActive = true;
    currentSnapshot_.sampleClipCount += clippedSamples;
    const auto overDb = 20.0 * std::log10(maximumMagnitude);
    if (std::isfinite(overDb)
        && (! currentSnapshot_.maxSampleOverDb.valid
            || overDb > currentSnapshot_.maxSampleOverDb.value))
        currentSnapshot_.maxSampleOverDb = { overDb, true };
}

void AnalysisCoordinator::process(const float* const* channels,
                                  const int numChannels,
                                  const int numSamples) noexcept
{
    if (! prepared_ || channels == nullptr || numChannels <= 0 || numSamples <= 0)
        return;

    if (resetRequested_.exchange(false, std::memory_order_acq_rel))
        resetOnAudioThread();

    const auto blockHasSignal = bufferHasSignal(channels, numChannels, numSamples);
    updateClipState(channels, numChannels, numSamples);
    if (blockHasSignal)
    {
        signalHoldRemainingFrames_ = signalHoldFrames_;
        currentSnapshot_.hasSignal = true;
    }
    else if (signalHoldRemainingFrames_ > static_cast<std::uint64_t>(numSamples))
    {
        signalHoldRemainingFrames_ -= static_cast<std::uint64_t>(numSamples);
    }
    else
    {
        signalHoldRemainingFrames_ = 0;
        currentSnapshot_.hasSignal = false;
    }

    dsp::LevelResult level;
    if (levelAnalyzer_.process(channels, numChannels, numSamples, level)
        && level.valid && blockHasSignal)
    {
        currentSnapshot_.samplePeakDbfs = { level.samplePeakDbfs, true };
        currentSnapshot_.rmsDbfs = { level.rmsDbfs, true };
        currentSnapshot_.crestDb = { level.crestDb, true };
    }

    dsp::LoudnessResult loudness;
    if (loudnessAnalyzer_.process(channels, numChannels, numSamples, loudness)
        && loudness.valid && blockHasSignal)
        currentSnapshot_.shortTermLufs = { loudness.shortTermLufs, true };

    dsp::StereoResult stereo;
    if (stereoAnalyzer_.process(channels, numChannels, numSamples, stereo) && blockHasSignal)
    {
        if (stereo.widthValid)
            currentSnapshot_.width = { stereo.width, true };
        if (stereo.correlationValid)
            currentSnapshot_.correlation = { stereo.correlation, true };
    }

    if (spectrumAnalyzer_.process(channels, numChannels, numSamples, spectrumResult_)
        && blockHasSignal)
    {
        currentSnapshot_.spectrumBinWidthHz = {
            spectrumResult_.binWidthHz, spectrumResult_.binWidthValid
        };
        for (std::size_t bin = 0; bin < spectrumResult_.binDbfs.size(); ++bin)
        {
            currentSnapshot_.spectrumBins[bin] = spectrumResult_.binValid[bin]
                ? MetricValue { spectrumResult_.binDbfs[bin], true }
                : MetricValue {};
        }
        for (std::size_t band = 0; band < spectrumResult_.bandDbfs.size(); ++band)
        {
            currentSnapshot_.spectrumBands[band] = spectrumResult_.bandValid[band]
                ? MetricValue { spectrumResult_.bandDbfs[band], true }
                : MetricValue {};
        }
    }

    currentSnapshot_.audioSampleClock += static_cast<std::uint64_t>(numSamples);
    currentSnapshot_.elapsedSeconds = static_cast<double>(currentSnapshot_.audioSampleClock)
        / sampleRate_;
    ++currentSnapshot_.sequence;
    publishedSnapshot_.publish(currentSnapshot_);
}

AnalysisSnapshot AnalysisCoordinator::getSnapshot() const noexcept
{
    if (resetRequested_.load(std::memory_order_acquire))
        return {};
    return publishedSnapshot_.load();
}
} // namespace aifred::analysis
