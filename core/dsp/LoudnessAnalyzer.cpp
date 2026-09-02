#include "LoudnessAnalyzer.h"

#include <algorithm>
#include <cmath>

namespace aifred::dsp
{
namespace
{
constexpr double pi = 3.14159265358979323846;

double finiteSample(const float value) noexcept
{
    return std::isfinite(value) ? static_cast<double>(value) : 0.0;
}
}

double LoudnessAnalyzer::BiquadState::process(
    const double sample, const BiquadCoefficients& coefficients) noexcept
{
    const auto output = coefficients.b0 * sample + z1;
    z1 = coefficients.b1 * sample - coefficients.a1 * output + z2;
    z2 = coefficients.b2 * sample - coefficients.a2 * output;
    return output;
}

void LoudnessAnalyzer::BiquadState::reset() noexcept
{
    z1 = 0.0;
    z2 = 0.0;
}

LoudnessAnalyzer::BiquadCoefficients LoudnessAnalyzer::makeKWeightingShelf(
    const double sampleRate) noexcept
{
    // Standards-derived digital reconstruction of the BS.1770 K-weighting
    // head-model shelf. It reproduces the ITU-R BS.1770-5 Table 1 response at
    // 48 kHz and preserves that response at other host sample rates.
    constexpr double frequency = 1681.974450955533;
    constexpr double gainDb = 3.999843853973347;
    constexpr double q = 0.7071752369554196;
    constexpr double exponent = 0.4996667741545416;

    const auto k = std::tan(pi * frequency / sampleRate);
    const auto vh = std::pow(10.0, gainDb / 20.0);
    const auto vb = std::pow(vh, exponent);
    const auto denominator = 1.0 + k / q + k * k;

    return {
        (vh + vb * k / q + k * k) / denominator,
        2.0 * (k * k - vh) / denominator,
        (vh - vb * k / q + k * k) / denominator,
        2.0 * (k * k - 1.0) / denominator,
        (1.0 - k / q + k * k) / denominator,
    };
}

LoudnessAnalyzer::BiquadCoefficients LoudnessAnalyzer::makeKWeightingHighPass(
    const double sampleRate) noexcept
{
    // Standards-derived digital reconstruction of the BS.1770 RLB stage.
    constexpr double frequency = 38.13547087602444;
    constexpr double q = 0.5003270373238773;

    const auto k = std::tan(pi * frequency / sampleRate);
    const auto denominator = 1.0 + k / q + k * k;
    return {
        1.0 / denominator,
        -2.0 / denominator,
        1.0 / denominator,
        2.0 * (k * k - 1.0) / denominator,
        (1.0 - k / q + k * k) / denominator,
    };
}

void LoudnessAnalyzer::prepare(const double sampleRate, const int numChannels)
{
    const auto safeRate = std::max(8000.0, sampleRate);
    const auto safeChannels = static_cast<std::size_t>(std::clamp(numChannels, 1, 2));
    const auto windowFrames = static_cast<std::size_t>(
        std::max(1.0, std::round(safeRate * shortTermWindowSeconds)));

    shelfCoefficients_ = makeKWeightingShelf(safeRate);
    highPassCoefficients_ = makeKWeightingHighPass(safeRate);
    channelFilters_.assign(safeChannels, {});
    frameEnergyRing_.assign(windowFrames, 0.0);
    updateFrames_ = static_cast<std::uint64_t>(
        std::max(1.0, std::round(safeRate * updateIntervalSeconds)));
    reset();
}

void LoudnessAnalyzer::reset() noexcept
{
    for (auto& channel : channelFilters_)
    {
        channel.shelf.reset();
        channel.highPass.reset();
    }
    std::fill(frameEnergyRing_.begin(), frameEnergyRing_.end(), 0.0);
    writeIndex_ = 0;
    framesSeen_ = 0;
    framesSinceUpdate_ = 0;
    energySum_ = 0.0;
}

bool LoudnessAnalyzer::process(const float* const* channels,
                               const int numChannels,
                               const int numSamples,
                               LoudnessResult& result) noexcept
{
    if (channels == nullptr || numChannels <= 0 || numSamples <= 0
        || channelFilters_.empty() || frameEnergyRing_.empty())
        return false;

    const auto channelsToMeasure = std::min<int>(numChannels,
                                                  static_cast<int>(channelFilters_.size()));
    bool produced = false;

    for (int frame = 0; frame < numSamples; ++frame)
    {
        double frameEnergy = 0.0;
        for (int channel = 0; channel < channelsToMeasure; ++channel)
        {
            const auto input = channels[channel] != nullptr
                                   ? finiteSample(channels[channel][frame])
                                   : 0.0;
            auto& filter = channelFilters_[static_cast<std::size_t>(channel)];
            const auto shelfOutput = filter.shelf.process(input, shelfCoefficients_);
            const auto weighted = filter.highPass.process(shelfOutput, highPassCoefficients_);
            frameEnergy += weighted * weighted; // L/R weights are both 1.0.
        }

        energySum_ += frameEnergy - frameEnergyRing_[writeIndex_];
        frameEnergyRing_[writeIndex_] = frameEnergy;
        writeIndex_ = (writeIndex_ + 1) % frameEnergyRing_.size();
        ++framesSeen_;

        if (++framesSinceUpdate_ >= updateFrames_)
        {
            framesSinceUpdate_ = 0;
            if (framesSeen_ >= frameEnergyRing_.size())
            {
                const auto meanWeightedEnergy = energySum_
                    / static_cast<double>(frameEnergyRing_.size());
                if (meanWeightedEnergy > 0.0 && std::isfinite(meanWeightedEnergy))
                {
                    // ITU-R BS.1770-5 Annex 1, equation 2, over a 3 s window.
                    result.shortTermLufs = -0.691 + 10.0 * std::log10(meanWeightedEnergy);
                    result.valid = std::isfinite(result.shortTermLufs);
                    produced = result.valid;
                }
            }
        }
    }

    return produced;
}
} // namespace aifred::dsp
