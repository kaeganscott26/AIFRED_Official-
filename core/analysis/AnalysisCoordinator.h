#pragma once

#include "AnalysisSnapshot.h"
#include "core/dsp/LevelAnalyzer.h"
#include "core/dsp/LoudnessAnalyzer.h"
#include "core/dsp/SpectrumAnalyzer.h"
#include "core/dsp/StereoAnalyzer.h"

#include <array>
#include <atomic>
#include <cstdint>

namespace aifred::analysis
{
class AnalysisCoordinator
{
public:
    AnalysisCoordinator() noexcept;

    void prepare(double sampleRate, int maxBlockSize, int numChannels);
    void reset() noexcept;
    void process(const float* const* channels, int numChannels, int numSamples) noexcept;
    [[nodiscard]] AnalysisSnapshot getSnapshot() const noexcept;

private:
    class AtomicSnapshotStorage
    {
    public:
        AtomicSnapshotStorage() noexcept;
        void publish(const AnalysisSnapshot& snapshot) noexcept;
        [[nodiscard]] AnalysisSnapshot load() const noexcept;

    private:
        static std::uint64_t encodeDouble(double value) noexcept;
        static double decodeDouble(std::uint64_t value) noexcept;
        static void storeMetric(std::atomic<std::uint64_t>& value,
                                std::atomic<std::uint64_t>& valid,
                                const MetricValue& metric) noexcept;
        static MetricValue loadMetric(const std::atomic<std::uint64_t>& value,
                                      const std::atomic<std::uint64_t>& valid) noexcept;

        mutable std::atomic<std::uint64_t> guard_ { 0 };
        std::atomic<std::uint64_t> sequence_ { 0 };
        std::atomic<std::uint64_t> audioSampleClock_ { 0 };
        std::atomic<std::uint64_t> elapsedSeconds_ { 0 };
        std::atomic<std::uint64_t> hasSignal_ { 0 };
        std::atomic<std::uint64_t> sampleClipActive_ { 0 };
        std::atomic<std::uint64_t> sampleClipCount_ { 0 };
        std::array<std::atomic<std::uint64_t>, 7> metricValues_;
        std::array<std::atomic<std::uint64_t>, 7> metricValidity_;
        std::atomic<std::uint64_t> spectrumBinWidthValue_ { 0 };
        std::atomic<std::uint64_t> spectrumBinWidthValidity_ { 0 };
        std::array<std::atomic<std::uint64_t>, AnalysisSnapshot::spectrumBinCount> binValues_;
        std::array<std::atomic<std::uint64_t>, AnalysisSnapshot::spectrumBinCount> binValidity_;
        std::array<std::atomic<std::uint64_t>, AnalysisSnapshot::spectrumBandCount> bandValues_;
        std::array<std::atomic<std::uint64_t>, AnalysisSnapshot::spectrumBandCount> bandValidity_;
    };

    void resetOnAudioThread() noexcept;
    [[nodiscard]] bool bufferHasSignal(const float* const* channels,
                                       int numChannels,
                                       int numSamples) const noexcept;
    void updateClipState(const float* const* channels,
                         int numChannels,
                         int numSamples) noexcept;

    static constexpr double signalFloorLinear = 0.000251188643150958; // -72 dBFS
    static constexpr double signalHoldSeconds = 0.5;

    dsp::LevelAnalyzer levelAnalyzer_;
    dsp::LoudnessAnalyzer loudnessAnalyzer_;
    dsp::StereoAnalyzer stereoAnalyzer_;
    dsp::SpectrumAnalyzer spectrumAnalyzer_;
    dsp::SpectrumResult spectrumResult_;

    AtomicSnapshotStorage publishedSnapshot_;
    std::atomic<bool> resetRequested_ { false };
    AnalysisSnapshot currentSnapshot_;
    double sampleRate_ = 48000.0;
    std::uint64_t signalHoldFrames_ = 24000;
    std::uint64_t signalHoldRemainingFrames_ = 0;
    bool prepared_ = false;
};
} // namespace aifred::analysis
