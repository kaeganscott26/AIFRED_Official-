#include "LevelAnalyzer.h"

#include <algorithm>
#include <cmath>

namespace aifred::dsp
{
namespace
{
double finiteSample(const float value) noexcept
{
    return std::isfinite(value) ? static_cast<double>(value) : 0.0;
}
}

void LevelAnalyzer::prepare(const double sampleRate) noexcept
{
    windowFrames_ = static_cast<std::uint64_t>(
        std::max(1.0, std::round(sampleRate * measurementWindowSeconds)));
    reset();
}

void LevelAnalyzer::reset() noexcept
{
    framesAccumulated_ = 0;
    samplesAccumulated_ = 0;
    peakLinear_ = 0.0;
    sumSquares_ = 0.0;
}

bool LevelAnalyzer::process(const float* const* channels,
                            const int numChannels,
                            const int numSamples,
                            LevelResult& result) noexcept
{
    bool produced = false;
    if (channels == nullptr || numChannels <= 0 || numSamples <= 0)
        return false;

    for (int frame = 0; frame < numSamples; ++frame)
    {
        for (int channel = 0; channel < numChannels; ++channel)
        {
            const auto sample = channels[channel] != nullptr
                                    ? finiteSample(channels[channel][frame])
                                    : 0.0;
            peakLinear_ = std::max(peakLinear_, std::abs(sample));
            sumSquares_ += sample * sample;
            ++samplesAccumulated_;
        }

        if (++framesAccumulated_ >= windowFrames_)
        {
            const auto rms = samplesAccumulated_ > 0
                                 ? std::sqrt(sumSquares_ / static_cast<double>(samplesAccumulated_))
                                 : 0.0;

            if (peakLinear_ > 0.0 && rms > 0.0)
            {
                result.samplePeakDbfs = 20.0 * std::log10(peakLinear_);
                result.rmsDbfs = 20.0 * std::log10(rms);
                result.crestDb = result.samplePeakDbfs - result.rmsDbfs;
                result.valid = true;
                produced = true;
            }

            framesAccumulated_ = 0;
            samplesAccumulated_ = 0;
            peakLinear_ = 0.0;
            sumSquares_ = 0.0;
        }
    }

    return produced;
}
} // namespace aifred::dsp
