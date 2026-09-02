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

    if (test.failures == 0)
    {
        std::cout << "AIFRED DSP smoke: PASS\n";
        return EXIT_SUCCESS;
    }

    std::cerr << "AIFRED DSP smoke: " << test.failures << " failure(s)\n";
    return EXIT_FAILURE;
}
