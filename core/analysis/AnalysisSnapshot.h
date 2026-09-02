#pragma once

#include <array>
#include <cstdint>

namespace aifred::analysis
{
struct MetricValue
{
    double value = 0.0;
    bool valid = false;
};

// A coherent, read-only copy of the latest analysis state. Raw values retain
// their measurement units; presentation scaling belongs to the UI.
struct AnalysisSnapshot
{
    static constexpr std::size_t spectrumFftSize = 2048;
    static constexpr std::size_t spectrumBinCount = spectrumFftSize / 2 + 1;
    static constexpr std::size_t spectrumBandCount = 7;

    std::uint64_t sequence = 0;
    std::uint64_t audioSampleClock = 0;
    double elapsedSeconds = 0.0;
    bool hasSignal = false;

    MetricValue samplePeakDbfs;
    MetricValue rmsDbfs;
    MetricValue crestDb;
    MetricValue shortTermLufs;
    MetricValue width;       // M/S side-energy share in [0, 1].
    MetricValue correlation; // Normalized L/R correlation in [-1, 1].

    // Full Hann-windowed FFT bin peak amplitudes in dBFS. Bin i is centered at
    // i * spectrumBinWidthHz. Values are measured facts with no per-mix or
    // display normalization, so this array also provides a direct DSP trace.
    MetricValue spectrumBinWidthHz;
    std::array<MetricValue, spectrumBinCount> spectrumBins {};

    // Hann-windowed FFT band RMS estimates in dBFS.
    std::array<MetricValue, spectrumBandCount> spectrumBands {};
};
} // namespace aifred::analysis
