#include "SpectrumAnalyzer.h"

#include <algorithm>
#include <cmath>

namespace aifred::dsp
{
namespace
{
constexpr double pi = 3.14159265358979323846;
constexpr double smoothingCoefficient = 0.65;
constexpr double hannEquivalentNoiseBandwidth = 1.5;

double finiteSample(const float value) noexcept
{
    return std::isfinite(value) ? static_cast<double>(value) : 0.0;
}
}

void SpectrumAnalyzer::prepare(const double sampleRate)
{
    sampleRate_ = std::max(8000.0, sampleRate);
    input_.assign(fftSize, 0.0);
    window_.resize(fftSize);
    real_.assign(fftSize, 0.0);
    imaginary_.assign(fftSize, 0.0);

    windowSum_ = 0.0;
    for (std::size_t index = 0; index < fftSize; ++index)
    {
        window_[index] = 0.5 - 0.5 * std::cos(
            2.0 * pi * static_cast<double>(index) / static_cast<double>(fftSize - 1));
        windowSum_ += window_[index];
    }
    reset();
}

void SpectrumAnalyzer::reset() noexcept
{
    std::fill(input_.begin(), input_.end(), 0.0);
    std::fill(real_.begin(), real_.end(), 0.0);
    std::fill(imaginary_.begin(), imaginary_.end(), 0.0);
    smoothedMeanSquare_.fill(0.0);
    inputIndex_ = 0;
    hasPreviousSpectrum_ = false;
}

bool SpectrumAnalyzer::process(const float* const* channels,
                               const int numChannels,
                               const int numSamples,
                               SpectrumResult& result) noexcept
{
    if (channels == nullptr || numChannels <= 0 || channels[0] == nullptr
        || numSamples <= 0 || input_.size() != fftSize)
        return false;

    bool produced = false;
    for (int frame = 0; frame < numSamples; ++frame)
    {
        input_[inputIndex_++] = finiteSample(channels[0][frame]);
        if (inputIndex_ == fftSize)
        {
            inputIndex_ = 0;
            transform();
            calculateBands(result);
            produced = true;
        }
    }
    return produced;
}

void SpectrumAnalyzer::transform() noexcept
{
    for (std::size_t index = 0; index < fftSize; ++index)
    {
        real_[index] = input_[index] * window_[index];
        imaginary_[index] = 0.0;
    }

    // In-place radix-2 Cooley-Tukey FFT. All storage was allocated in prepare().
    std::size_t reversed = 0;
    for (std::size_t index = 1; index < fftSize; ++index)
    {
        auto bit = fftSize >> 1U;
        while ((reversed & bit) != 0U)
        {
            reversed ^= bit;
            bit >>= 1U;
        }
        reversed ^= bit;
        if (index < reversed)
        {
            std::swap(real_[index], real_[reversed]);
            std::swap(imaginary_[index], imaginary_[reversed]);
        }
    }

    for (std::size_t length = 2; length <= fftSize; length <<= 1U)
    {
        const auto angle = -2.0 * pi / static_cast<double>(length);
        const auto stepReal = std::cos(angle);
        const auto stepImaginary = std::sin(angle);

        for (std::size_t start = 0; start < fftSize; start += length)
        {
            double twiddleReal = 1.0;
            double twiddleImaginary = 0.0;
            const auto halfLength = length >> 1U;
            for (std::size_t offset = 0; offset < halfLength; ++offset)
            {
                const auto even = start + offset;
                const auto odd = even + halfLength;
                const auto oddReal = real_[odd] * twiddleReal
                    - imaginary_[odd] * twiddleImaginary;
                const auto oddImaginary = real_[odd] * twiddleImaginary
                    + imaginary_[odd] * twiddleReal;
                const auto evenReal = real_[even];
                const auto evenImaginary = imaginary_[even];

                real_[even] = evenReal + oddReal;
                imaginary_[even] = evenImaginary + oddImaginary;
                real_[odd] = evenReal - oddReal;
                imaginary_[odd] = evenImaginary - oddImaginary;

                const auto nextReal = twiddleReal * stepReal
                    - twiddleImaginary * stepImaginary;
                twiddleImaginary = twiddleReal * stepImaginary
                    + twiddleImaginary * stepReal;
                twiddleReal = nextReal;
            }
        }
    }
}

void SpectrumAnalyzer::calculateBands(SpectrumResult& result) noexcept
{
    const auto binWidth = sampleRate_ / static_cast<double>(fftSize);
    const auto nyquist = sampleRate_ * 0.5;

    for (std::size_t band = 0; band < SpectrumResult::bandCount; ++band)
    {
        const auto low = bandEdgesHz[band];
        const auto high = std::min(bandEdgesHz[band + 1], nyquist);
        double bandMeanSquare = 0.0;

        if (high > low)
        {
            auto firstBin = static_cast<std::size_t>(std::ceil(low / binWidth));
            auto lastBin = static_cast<std::size_t>(std::floor(high / binWidth));
            firstBin = std::max<std::size_t>(1, firstBin);
            lastBin = std::min<std::size_t>(fftSize / 2, lastBin);

            for (auto bin = firstBin; bin <= lastBin && firstBin <= lastBin; ++bin)
            {
                const auto magnitudeSquared = real_[bin] * real_[bin]
                    + imaginary_[bin] * imaginary_[bin];
                const auto peakAmplitudeSquared = 4.0 * magnitudeSquared
                    / (windowSum_ * windowSum_);
                bandMeanSquare += peakAmplitudeSquared * 0.5;
            }
            bandMeanSquare /= hannEquivalentNoiseBandwidth;
        }

        if (hasPreviousSpectrum_)
        {
            smoothedMeanSquare_[band] = smoothingCoefficient * smoothedMeanSquare_[band]
                + (1.0 - smoothingCoefficient) * bandMeanSquare;
        }
        else
        {
            smoothedMeanSquare_[band] = bandMeanSquare;
        }

        result.valid[band] = smoothedMeanSquare_[band] > 0.0
            && std::isfinite(smoothedMeanSquare_[band]);
        if (result.valid[band])
            result.bandDbfs[band] = 10.0 * std::log10(smoothedMeanSquare_[band]);
    }

    hasPreviousSpectrum_ = true;
}
} // namespace aifred::dsp
