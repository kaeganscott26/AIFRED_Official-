#pragma once

#include <array>
#include <cstddef>
#include <vector>

namespace aifred::dsp
{
struct SpectrumResult
{
    static constexpr std::size_t fftSize = 2048;
    static constexpr std::size_t binCount = fftSize / 2 + 1;
    static constexpr std::size_t bandCount = 7;

    double binWidthHz = 0.0;
    bool binWidthValid = false;
    std::array<double, binCount> binDbfs {};
    std::array<bool, binCount> binValid {};
    std::array<double, bandCount> bandDbfs {};
    std::array<bool, bandCount> bandValid {};
};

class SpectrumAnalyzer
{
public:
    static constexpr std::size_t fftSize = SpectrumResult::fftSize;
    static constexpr std::array<double, SpectrumResult::bandCount> bandLabelsHz {
        60.0, 120.0, 250.0, 500.0, 1000.0, 4000.0, 10000.0
    };

    void prepare(double sampleRate);
    void reset() noexcept;

    // Stereo is reduced to an energy-preserving mono analysis signal using
    // (L + R) / sqrt(2). Mono uses channel 0 unchanged. Full-resolution bins
    // and the compatibility bands come from this same windowed FFT signal.
    bool process(const float* const* channels,
                 int numChannels,
                 int numSamples,
                 SpectrumResult& result) noexcept;

private:
    void transform() noexcept;
    void calculateBins(SpectrumResult& result) noexcept;
    void calculateBands(SpectrumResult& result) noexcept;

    static constexpr std::array<double, SpectrumResult::bandCount + 1> bandEdgesHz {
        20.0, 90.0, 180.0, 375.0, 750.0, 2000.0, 7000.0, 20000.0
    };

    double sampleRate_ = 48000.0;
    double windowSum_ = 1.0;
    std::vector<double> input_;
    std::vector<double> window_;
    std::vector<double> real_;
    std::vector<double> imaginary_;
    std::array<double, SpectrumResult::bandCount> smoothedMeanSquare_ {};
    std::size_t inputIndex_ = 0;
    bool hasPreviousSpectrum_ = false;
};
} // namespace aifred::dsp
