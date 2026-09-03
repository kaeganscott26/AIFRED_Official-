#include "core/analysis/AnalysisCoordinator.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace
{
constexpr double sampleRate = 48000.0;
constexpr int blockSize = 512;
constexpr double pi = 3.14159265358979323846;

struct SmokeTest
{
    int failures = 0;

    void expect(const bool condition, const std::string& message)
    {
        if (! condition)
        {
            ++failures;
            std::cerr << "FAIL: " << message << '\n';
        }
    }
};

void feedSine(aifred::analysis::AnalysisCoordinator& coordinator,
              const double frequency,
              const double amplitude,
              const double seconds,
              const bool invertRight = false)
{
    std::vector<float> left(blockSize);
    std::vector<float> right(blockSize);
    const float* channels[] { left.data(), right.data() };
    const auto totalFrames = static_cast<std::uint64_t>(std::round(seconds * sampleRate));
    std::uint64_t frameClock = 0;

    while (frameClock < totalFrames)
    {
        const auto frames = static_cast<int>(
            std::min<std::uint64_t>(blockSize, totalFrames - frameClock));
        for (int frame = 0; frame < frames; ++frame)
        {
            const auto phase = 2.0 * pi * frequency
                * static_cast<double>(frameClock + static_cast<std::uint64_t>(frame))
                / sampleRate;
            left[static_cast<std::size_t>(frame)] = static_cast<float>(amplitude * std::sin(phase));
            right[static_cast<std::size_t>(frame)] = invertRight
                ? -left[static_cast<std::size_t>(frame)]
                : left[static_cast<std::size_t>(frame)];
        }
        coordinator.process(channels, 2, frames);
        frameClock += static_cast<std::uint64_t>(frames);
    }
}

void feedMonoSine(aifred::analysis::AnalysisCoordinator& coordinator,
                  const double frequency,
                  const double amplitude,
                  const double seconds)
{
    std::vector<float> mono(blockSize);
    const float* channels[] { mono.data() };
    const auto totalFrames = static_cast<std::uint64_t>(std::round(seconds * sampleRate));
    std::uint64_t frameClock = 0;

    while (frameClock < totalFrames)
    {
        const auto frames = static_cast<int>(
            std::min<std::uint64_t>(blockSize, totalFrames - frameClock));
        for (int frame = 0; frame < frames; ++frame)
        {
            const auto phase = 2.0 * pi * frequency
                * static_cast<double>(frameClock + static_cast<std::uint64_t>(frame))
                / sampleRate;
            mono[static_cast<std::size_t>(frame)] = static_cast<float>(amplitude * std::sin(phase));
        }
        coordinator.process(channels, 1, frames);
        frameClock += static_cast<std::uint64_t>(frames);
    }
}

void feedStereoSine(aifred::analysis::AnalysisCoordinator& coordinator,
                    const double frequency,
                    const double leftAmplitude,
                    const double rightAmplitude,
                    const double seconds)
{
    std::vector<float> left(blockSize);
    std::vector<float> right(blockSize);
    const float* channels[] { left.data(), right.data() };
    const auto totalFrames = static_cast<std::uint64_t>(std::round(seconds * sampleRate));
    std::uint64_t frameClock = 0;

    while (frameClock < totalFrames)
    {
        const auto frames = static_cast<int>(
            std::min<std::uint64_t>(blockSize, totalFrames - frameClock));
        for (int frame = 0; frame < frames; ++frame)
        {
            const auto phase = 2.0 * pi * frequency
                * static_cast<double>(frameClock + static_cast<std::uint64_t>(frame))
                / sampleRate;
            const auto sine = std::sin(phase);
            left[static_cast<std::size_t>(frame)] = static_cast<float>(leftAmplitude * sine);
            right[static_cast<std::size_t>(frame)] = static_cast<float>(rightAmplitude * sine);
        }
        coordinator.process(channels, 2, frames);
        frameClock += static_cast<std::uint64_t>(frames);
    }
}

void feedTwoToneMix(aifred::analysis::AnalysisCoordinator& coordinator,
                    const double lowAmplitude,
                    const double highAmplitude,
                    const double seconds)
{
    std::vector<float> left(blockSize);
    std::vector<float> right(blockSize);
    const float* channels[] { left.data(), right.data() };
    const auto totalFrames = static_cast<std::uint64_t>(std::round(seconds * sampleRate));
    std::uint64_t frameClock = 0;

    while (frameClock < totalFrames)
    {
        const auto frames = static_cast<int>(
            std::min<std::uint64_t>(blockSize, totalFrames - frameClock));
        for (int frame = 0; frame < frames; ++frame)
        {
            const auto time = static_cast<double>(
                frameClock + static_cast<std::uint64_t>(frame)) / sampleRate;
            const auto sample = lowAmplitude * std::sin(2.0 * pi * 100.0 * time)
                + highAmplitude * std::sin(2.0 * pi * 1000.0 * time);
            left[static_cast<std::size_t>(frame)] = static_cast<float>(sample);
            right[static_cast<std::size_t>(frame)] = static_cast<float>(sample);
        }
        coordinator.process(channels, 2, frames);
        frameClock += static_cast<std::uint64_t>(frames);
    }
}

void feedSilence(aifred::analysis::AnalysisCoordinator& coordinator, const double seconds)
{
    std::vector<float> left(blockSize, 0.0F);
    std::vector<float> right(blockSize, 0.0F);
    const float* channels[] { left.data(), right.data() };
    auto remaining = static_cast<int>(std::round(seconds * sampleRate));
    while (remaining > 0)
    {
        const auto frames = std::min(blockSize, remaining);
        coordinator.process(channels, 2, frames);
        remaining -= frames;
    }
}

void feedClipSamples(aifred::analysis::AnalysisCoordinator& coordinator)
{
    std::vector<float> left(blockSize, 0.0F);
    std::vector<float> right(blockSize, 0.0F);
    left[0] = 1.0F;
    left[1] = -1.0F;
    right[0] = 2.0F;
    const float* channels[] { left.data(), right.data() };
    coordinator.process(channels, 2, blockSize);
}

bool near(const double actual, const double expected, const double tolerance)
{
    return std::abs(actual - expected) <= tolerance;
}

std::size_t strongestBand(const aifred::analysis::AnalysisSnapshot& snapshot)
{
    std::size_t strongest = 0;
    double strongestValue = -1000.0;
    for (std::size_t band = 0; band < snapshot.spectrumBands.size(); ++band)
    {
        if (snapshot.spectrumBands[band].valid
            && snapshot.spectrumBands[band].value > strongestValue)
        {
            strongestValue = snapshot.spectrumBands[band].value;
            strongest = band;
        }
    }
    return strongest;
}

std::size_t strongestSpectrumBin(const aifred::analysis::AnalysisSnapshot& snapshot)
{
    std::size_t strongest = 0;
    double strongestValue = -1000.0;
    if (! snapshot.spectrumBinWidthHz.valid)
        return strongest;

    for (std::size_t bin = 1; bin < snapshot.spectrumBins.size(); ++bin)
    {
        const auto frequency = static_cast<double>(bin) * snapshot.spectrumBinWidthHz.value;
        if (frequency < 20.0 || frequency > 20000.0)
            continue;
        if (snapshot.spectrumBins[bin].valid
            && snapshot.spectrumBins[bin].value > strongestValue)
        {
            strongestValue = snapshot.spectrumBins[bin].value;
            strongest = bin;
        }
    }
    return strongest;
}

double spectrumValueNear(const aifred::analysis::AnalysisSnapshot& snapshot,
                         const double frequency)
{
    if (! snapshot.spectrumBinWidthHz.valid || snapshot.spectrumBinWidthHz.value <= 0.0)
        return 0.0;
    const auto bin = static_cast<std::size_t>(std::llround(
        frequency / snapshot.spectrumBinWidthHz.value));
    if (bin >= snapshot.spectrumBins.size() || ! snapshot.spectrumBins[bin].valid)
        return 0.0;
    return snapshot.spectrumBins[bin].value;
}

void expectSpectrumPeakNear(SmokeTest& test,
                            const aifred::analysis::AnalysisSnapshot& snapshot,
                            const double expectedFrequency)
{
    test.expect(snapshot.spectrumBinWidthHz.valid,
                "spectrum must publish valid bin-frequency metadata");
    if (! snapshot.spectrumBinWidthHz.valid)
        return;

    const auto strongest = strongestSpectrumBin(snapshot);
    const auto actualFrequency = static_cast<double>(strongest)
        * snapshot.spectrumBinWidthHz.value;
    test.expect(std::abs(actualFrequency - expectedFrequency)
                    <= snapshot.spectrumBinWidthHz.value,
                "full-resolution spectrum peak must land within one FFT bin of the sine");
}
} // namespace

int main()
{
    SmokeTest test;
    aifred::analysis::AnalysisCoordinator coordinator;
    coordinator.prepare(sampleRate, blockSize, 2);

    feedSilence(coordinator, 1.0);
    auto snapshot = coordinator.getSnapshot();
    test.expect(! snapshot.hasSignal, "silence must not report signal");
    test.expect(! snapshot.samplePeakDbfs.valid, "silence peak must be unavailable, not a sentinel");
    test.expect(! snapshot.rmsDbfs.valid, "silence RMS must be unavailable, not a sentinel");
    test.expect(! snapshot.shortTermLufs.valid, "silence LUFS must be unavailable");
    test.expect(std::isfinite(snapshot.elapsedSeconds), "silence must not produce NaN elapsed time");

    coordinator.reset();
    feedSine(coordinator, 1000.0, 0.25, 3.3);
    snapshot = coordinator.getSnapshot();
    test.expect(snapshot.hasSignal, "sine must report active signal");
    test.expect(snapshot.samplePeakDbfs.valid && near(snapshot.samplePeakDbfs.value, -12.0412, 0.15),
                "sine peak must match amplitude in dBFS");
    test.expect(snapshot.rmsDbfs.valid && near(snapshot.rmsDbfs.value, -15.0515, 0.15),
                "sine RMS must be peak minus about 3.01 dB");
    test.expect(snapshot.crestDb.valid && near(snapshot.crestDb.value, 3.0103, 0.15),
                "sine crest factor must be about 3.01 dB");
    test.expect(snapshot.shortTermLufs.valid && std::isfinite(snapshot.shortTermLufs.value),
                "3 second K-weighted short-term loudness must become available");
    test.expect(snapshot.correlation.valid && snapshot.correlation.value > 0.999,
                "identical stereo correlation must approach +1");
    test.expect(snapshot.width.valid && snapshot.width.value < 0.001,
                "identical stereo width must approach zero");

    const auto basePeak = snapshot.samplePeakDbfs.value;
    const auto baseRms = snapshot.rmsDbfs.value;
    const auto baseCrest = snapshot.crestDb.value;

    coordinator.reset();
    feedClipSamples(coordinator);
    snapshot = coordinator.getSnapshot();
    test.expect(snapshot.sampleClipActive,
                "sample clip state must latch when magnitude reaches 0 dBFS");
    test.expect(snapshot.sampleClipCount == 3,
                "sample clip count must count actual clipped channel samples");
    test.expect(snapshot.maxSampleOverDb.valid && near(snapshot.maxSampleOverDb.value, 6.0206, 0.01),
                "maximum sample over must report dB above full scale");
    feedSilence(coordinator, 0.6);
    snapshot = coordinator.getSnapshot();
    test.expect(snapshot.sampleClipActive && snapshot.sampleClipCount == 3,
                "sample clip state must remain latched through silence");
    coordinator.reset();
    feedSilence(coordinator, 0.01);
    snapshot = coordinator.getSnapshot();
    test.expect(! snapshot.sampleClipActive && snapshot.sampleClipCount == 0
                    && ! snapshot.maxSampleOverDb.valid,
                "explicit analysis reset must clear the clip latch");

    coordinator.reset();
    feedSine(coordinator, 1000.0, 0.5, 1.0);
    snapshot = coordinator.getSnapshot();
    test.expect(near(snapshot.samplePeakDbfs.value - basePeak, 6.0206, 0.15),
                "+6 dB gain must raise peak by about 6 dB");
    test.expect(near(snapshot.rmsDbfs.value - baseRms, 6.0206, 0.15),
                "+6 dB gain must raise RMS by about 6 dB");
    test.expect(near(snapshot.crestDb.value, baseCrest, 0.1),
                "gain-only change must preserve crest factor");

    coordinator.reset();
    feedSine(coordinator, 1000.0, 0.25, 0.6, true);
    snapshot = coordinator.getSnapshot();
    test.expect(snapshot.correlation.valid && snapshot.correlation.value < -0.999,
                "polarity-inverted stereo correlation must approach -1");
    test.expect(snapshot.width.valid && snapshot.width.value > 0.999,
                "polarity-inverted stereo must not look mono");

    coordinator.reset();
    feedSine(coordinator, 60.0, 0.25, 0.5);
    snapshot = coordinator.getSnapshot();
    test.expect(strongestBand(snapshot) == 0,
                "60 Hz sine must dominate the lowest displayed spectrum band");

    coordinator.reset();
    feedSine(coordinator, 10000.0, 0.25, 0.5);
    snapshot = coordinator.getSnapshot();
    test.expect(strongestBand(snapshot) == 6,
                "10 kHz sine must dominate the highest displayed spectrum band");

    for (const auto frequency : { 100.0, 1000.0, 10000.0 })
    {
        coordinator.reset();
        feedSine(coordinator, frequency, 0.25, 0.6);
        snapshot = coordinator.getSnapshot();
        expectSpectrumPeakNear(test, snapshot, frequency);
    }

    coordinator.reset();
    feedTwoToneMix(coordinator, 0.1, 0.1, 0.6);
    const auto flatSpectrum = coordinator.getSnapshot();
    coordinator.reset();
    feedTwoToneMix(coordinator, 0.1, 0.1 * std::pow(10.0, 3.0 / 20.0), 0.6);
    const auto boostedSpectrum = coordinator.getSnapshot();
    test.expect(near(spectrumValueNear(boostedSpectrum, 1000.0)
                         - spectrumValueNear(flatSpectrum, 1000.0),
                     3.0, 0.15),
                "+3 dB movement at 1 kHz must remain visible in raw spectrum bins");
    test.expect(near(spectrumValueNear(boostedSpectrum, 100.0)
                         - spectrumValueNear(flatSpectrum, 100.0),
                     0.0, 0.15),
                "a 1 kHz gain change must not normalize the unchanged 100 Hz spectrum bin");

    coordinator.reset();
    feedMonoSine(coordinator, 1000.0, 0.25, 0.6);
    const auto monoSpectrum = coordinator.getSnapshot();
    coordinator.reset();
    feedStereoSine(coordinator, 1000.0, 0.25, 0.25, 0.6);
    const auto identicalStereoSpectrum = coordinator.getSnapshot();
    test.expect(near(spectrumValueNear(identicalStereoSpectrum, 1000.0)
                         - spectrumValueNear(monoSpectrum, 1000.0),
                     3.0103, 0.15),
                "(L + R) / sqrt(2) must add identical stereo by about 3.01 dB");

    coordinator.reset();
    feedStereoSine(coordinator, 1000.0, 0.0, 0.25, 0.6);
    const auto rightOnlySpectrum = coordinator.getSnapshot();
    expectSpectrumPeakNear(test, rightOnlySpectrum, 1000.0);
    test.expect(near(spectrumValueNear(rightOnlySpectrum, 1000.0)
                         - spectrumValueNear(monoSpectrum, 1000.0),
                     -3.0103, 0.15),
                "right-only stereo must contribute through the documented mono spectrum signal");

    if (test.failures == 0)
    {
        std::cout << "AIFRED DSP smoke: PASS\n";
        return EXIT_SUCCESS;
    }

    std::cerr << "AIFRED DSP smoke: " << test.failures << " failure(s)\n";
    return EXIT_FAILURE;
}
