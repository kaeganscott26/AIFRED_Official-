#pragma once

#include <cstdint>
#include <vector>

namespace aifred::dsp
{
struct StereoResult
{
    double width = 0.0;
    double correlation = 0.0;
    bool widthValid = false;
    bool correlationValid = false;
};

class StereoAnalyzer
{
public:
    void prepare(double sampleRate);
    void reset() noexcept;

    bool process(const float* const* channels,
                 int numChannels,
                 int numSamples,
                 StereoResult& result) noexcept;

private:
    static constexpr double measurementWindowSeconds = 0.4;
    static constexpr double updateIntervalSeconds = 0.1;

    std::vector<double> leftSquares_;
    std::vector<double> rightSquares_;
    std::vector<double> crossProducts_;
    std::vector<double> midSquares_;
    std::vector<double> sideSquares_;
    std::size_t writeIndex_ = 0;
    std::uint64_t framesSeen_ = 0;
    std::uint64_t framesSinceUpdate_ = 0;
    std::uint64_t updateFrames_ = 1;
    double leftSum_ = 0.0;
    double rightSum_ = 0.0;
    double crossSum_ = 0.0;
    double midSum_ = 0.0;
    double sideSum_ = 0.0;
};
} // namespace aifred::dsp
