#include "StereoAnalyzer.h"

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

void StereoAnalyzer::prepare(const double sampleRate)
{
    const auto windowFrames = static_cast<std::size_t>(
        std::max(1.0, std::round(sampleRate * measurementWindowSeconds)));
    updateFrames_ = static_cast<std::uint64_t>(
        std::max(1.0, std::round(sampleRate * updateIntervalSeconds)));

    leftSquares_.assign(windowFrames, 0.0);
    rightSquares_.assign(windowFrames, 0.0);
    crossProducts_.assign(windowFrames, 0.0);
    midSquares_.assign(windowFrames, 0.0);
    sideSquares_.assign(windowFrames, 0.0);
    reset();
}

void StereoAnalyzer::reset() noexcept
{
    std::fill(leftSquares_.begin(), leftSquares_.end(), 0.0);
    std::fill(rightSquares_.begin(), rightSquares_.end(), 0.0);
    std::fill(crossProducts_.begin(), crossProducts_.end(), 0.0);
    std::fill(midSquares_.begin(), midSquares_.end(), 0.0);
    std::fill(sideSquares_.begin(), sideSquares_.end(), 0.0);
    writeIndex_ = 0;
    framesSeen_ = 0;
    framesSinceUpdate_ = 0;
    leftSum_ = rightSum_ = crossSum_ = midSum_ = sideSum_ = 0.0;
}

bool StereoAnalyzer::process(const float* const* channels,
                             const int numChannels,
                             const int numSamples,
                             StereoResult& result) noexcept
{
    if (channels == nullptr || numChannels <= 0 || numSamples <= 0 || leftSquares_.empty())
        return false;

    bool produced = false;
    constexpr auto inverseSqrtTwo = 0.7071067811865475244;

    for (int frame = 0; frame < numSamples; ++frame)
    {
        const auto left = channels[0] != nullptr ? finiteSample(channels[0][frame]) : 0.0;
        const auto right = numChannels > 1 && channels[1] != nullptr
                               ? finiteSample(channels[1][frame])
                               : left;
        const auto mid = (left + right) * inverseSqrtTwo;
        const auto side = (left - right) * inverseSqrtTwo;
        const auto leftSquare = left * left;
        const auto rightSquare = right * right;
        const auto cross = left * right;
        const auto midSquare = mid * mid;
        const auto sideSquare = side * side;

        leftSum_ += leftSquare - leftSquares_[writeIndex_];
        rightSum_ += rightSquare - rightSquares_[writeIndex_];
        crossSum_ += cross - crossProducts_[writeIndex_];
        midSum_ += midSquare - midSquares_[writeIndex_];
        sideSum_ += sideSquare - sideSquares_[writeIndex_];

        leftSquares_[writeIndex_] = leftSquare;
        rightSquares_[writeIndex_] = rightSquare;
        crossProducts_[writeIndex_] = cross;
        midSquares_[writeIndex_] = midSquare;
        sideSquares_[writeIndex_] = sideSquare;
        writeIndex_ = (writeIndex_ + 1) % leftSquares_.size();
        ++framesSeen_;

        if (++framesSinceUpdate_ >= updateFrames_)
        {
            framesSinceUpdate_ = 0;
            const auto midSideTotal = midSum_ + sideSum_;
            result.widthValid = midSideTotal > 0.0;
            if (result.widthValid)
                result.width = std::clamp(sideSum_ / midSideTotal, 0.0, 1.0);

            const auto denominator = std::sqrt(std::max(0.0, leftSum_ * rightSum_));
            result.correlationValid = denominator > 0.0;
            if (result.correlationValid)
                result.correlation = std::clamp(crossSum_ / denominator, -1.0, 1.0);

            produced = result.widthValid || result.correlationValid;
        }
    }

    return produced;
}
} // namespace aifred::dsp
