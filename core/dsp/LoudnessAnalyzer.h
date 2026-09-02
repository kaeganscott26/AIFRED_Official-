#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace aifred::dsp
{
struct LoudnessResult
{
    double shortTermLufs = 0.0;
    bool valid = false;
};

class LoudnessAnalyzer
{
public:
    void prepare(double sampleRate, int numChannels);
    void reset() noexcept;

    bool process(const float* const* channels,
                 int numChannels,
                 int numSamples,
                 LoudnessResult& result) noexcept;

private:
    struct BiquadCoefficients
    {
        double b0 = 1.0;
        double b1 = 0.0;
        double b2 = 0.0;
        double a1 = 0.0;
        double a2 = 0.0;
    };

    struct BiquadState
    {
        double z1 = 0.0;
        double z2 = 0.0;

        double process(double sample, const BiquadCoefficients& coefficients) noexcept;
        void reset() noexcept;
    };

    struct ChannelFilter
    {
        BiquadState shelf;
        BiquadState highPass;
    };

    static BiquadCoefficients makeKWeightingShelf(double sampleRate) noexcept;
    static BiquadCoefficients makeKWeightingHighPass(double sampleRate) noexcept;

    static constexpr double shortTermWindowSeconds = 3.0;
    static constexpr double updateIntervalSeconds = 0.1;

    BiquadCoefficients shelfCoefficients_;
    BiquadCoefficients highPassCoefficients_;
    std::vector<ChannelFilter> channelFilters_;
    std::vector<double> frameEnergyRing_;
    std::size_t writeIndex_ = 0;
    std::uint64_t framesSeen_ = 0;
    std::uint64_t framesSinceUpdate_ = 0;
    std::uint64_t updateFrames_ = 1;
    double energySum_ = 0.0;
};
} // namespace aifred::dsp
