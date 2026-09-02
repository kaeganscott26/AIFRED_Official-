#pragma once

#include <cstdint>

namespace aifred::dsp
{
struct LevelResult
{
    double samplePeakDbfs = 0.0;
    double rmsDbfs = 0.0;
    double crestDb = 0.0;
    bool valid = false;
};

class LevelAnalyzer
{
public:
    void prepare(double sampleRate) noexcept;
    void reset() noexcept;

    // Returns true when a complete, same-signal/same-window result is ready.
    bool process(const float* const* channels,
                 int numChannels,
                 int numSamples,
                 LevelResult& result) noexcept;

private:
    static constexpr double measurementWindowSeconds = 0.1;

    std::uint64_t windowFrames_ = 1;
    std::uint64_t framesAccumulated_ = 0;
    std::uint64_t samplesAccumulated_ = 0;
    double peakLinear_ = 0.0;
    double sumSquares_ = 0.0;
};
} // namespace aifred::dsp
