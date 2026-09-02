#include "core/analysis/ComparisonEngine.h"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

namespace
{
struct Test
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

bool near(const double actual, const double expected, const double tolerance = 1.0e-9)
{
    return std::abs(actual - expected) <= tolerance;
}

aifred::analysis::AnalysisSnapshot makeSnapshot(const double gainDb)
{
    using aifred::analysis::MetricValue;
    aifred::analysis::AnalysisSnapshot snapshot;
    snapshot.sequence = gainDb == 0.0 ? 10 : 20;
    snapshot.audioSampleClock = gainDb == 0.0 ? 48000 : 96000;
    snapshot.elapsedSeconds = gainDb == 0.0 ? 1.0 : 2.0;
    snapshot.hasSignal = true;
    snapshot.samplePeakDbfs = MetricValue { -12.0 + gainDb, true };
    snapshot.rmsDbfs = MetricValue { -15.0 + gainDb, true };
    snapshot.crestDb = MetricValue { 3.0, true };
    snapshot.shortTermLufs = MetricValue { -16.0 + gainDb, true };
    snapshot.width = MetricValue { 0.25, true };
    snapshot.correlation = MetricValue { 0.8, true };
    snapshot.spectrumBinWidthHz = MetricValue { 23.4375, true };
    for (std::size_t bin = 0; bin < snapshot.spectrumBins.size(); ++bin)
        snapshot.spectrumBins[bin] = MetricValue { -70.0 + gainDb, true };
    return snapshot;
}
} // namespace

int main()
{
    using namespace aifred::analysis;
    Test test;
    SnapshotCaptureModel captures;

    auto missing = ComparisonEngine::compare(captures);
    test.expect(missing.availability == ComparisonAvailability::missingBothSnapshots,
                "empty captures must report both snapshots missing");
    test.expect(! missing.samplePeakDbfs.delta.valid,
                "missing snapshots must not produce a metric delta");

    auto liveA = makeSnapshot(0.0);
    captures.captureA(liveA);
    liveA.samplePeakDbfs.value = 99.0;
    test.expect(captures.a()->samplePeakDbfs.value == -12.0,
                "capture A must own a frozen copy of its snapshot");

    auto oneSided = ComparisonEngine::compare(captures);
    test.expect(oneSided.availability == ComparisonAvailability::missingSnapshotB,
                "one-sided capture must identify missing B");
    test.expect(oneSided.samplePeakDbfs.a.valid && ! oneSided.samplePeakDbfs.delta.valid,
                "one-sided result must preserve A without inventing a delta");

    const auto snapshotB = makeSnapshot(6.0);
    captures.captureB(snapshotB);
    auto comparison = ComparisonEngine::compare(captures);
    test.expect(comparison.ready(), "two captures must make the comparison ready");
    test.expect(comparison.samplePeakDbfs.delta.valid
                    && near(comparison.samplePeakDbfs.delta.value, 6.0),
                "peak delta must be B minus A");
    test.expect(comparison.rmsDbfs.delta.valid
                    && near(comparison.rmsDbfs.delta.value, 6.0),
                "RMS delta must be B minus A");
    test.expect(comparison.crestDb.delta.valid
                    && near(comparison.crestDb.delta.value, 0.0),
                "gain-only comparison must preserve crest");
    test.expect(comparison.a->sequence == 10 && comparison.b->sequence == 20,
                "comparison result must preserve complete raw A and B snapshots");
    test.expect(comparison.spectrum.availability == ComparisonAvailability::available,
                "matching FFT grids must be comparable");
    test.expect(comparison.spectrum.deltaBins[100].valid
                    && near(comparison.spectrum.deltaBins[100].value, 6.0),
                "spectrum bins must expose measured B-minus-A deltas");

    auto invalidB = snapshotB;
    invalidB.shortTermLufs.valid = false;
    invalidB.spectrumBins[100].valid = false;
    auto invalidComparison = ComparisonEngine::compare(*captures.a(), invalidB);
    test.expect(invalidComparison.shortTermLufs.availability
                    == ComparisonAvailability::valueBInvalid,
                "metric comparison must identify invalid B values");
    test.expect(! invalidComparison.shortTermLufs.delta.valid,
                "an unavailable metric must never produce a numeric delta");
    test.expect(! invalidComparison.spectrum.deltaBins[100].valid,
                "an unavailable spectrum bin must never produce a numeric delta");
    test.expect(invalidComparison.spectrum.deltaBins[101].valid,
                "one unavailable bin must not suppress valid neighboring deltas");

    auto invalidA = *captures.a();
    invalidA.width.valid = false;
    auto bothInvalid = invalidB;
    bothInvalid.width.valid = false;
    auto bothInvalidComparison = ComparisonEngine::compare(invalidA, bothInvalid);
    test.expect(bothInvalidComparison.width.availability
                    == ComparisonAvailability::bothValuesInvalid,
                "metric comparison must distinguish two invalid raw values");
    test.expect(! bothInvalidComparison.width.delta.valid,
                "two unavailable values must not produce a delta");

    auto differentGrid = snapshotB;
    differentGrid.spectrumBinWidthHz.value = 21.533203125;
    auto gridComparison = ComparisonEngine::compare(*captures.a(), differentGrid);
    test.expect(gridComparison.spectrum.availability
                    == ComparisonAvailability::incompatibleSpectrumGrid,
                "different FFT grids must not be compared bin by bin");
    test.expect(! gridComparison.spectrum.deltaBins[100].valid,
                "incompatible grids must not produce spectral deltas");

    captures.swap();
    test.expect(captures.a()->sequence == 20 && captures.b()->sequence == 10,
                "swap must exchange the frozen A and B captures");
    captures.resetA();
    test.expect(! captures.hasA() && captures.hasB(), "reset A must preserve B");
    captures.resetB();
    test.expect(! captures.hasA() && ! captures.hasB(), "reset B must clear B");

    captures.captureA(makeSnapshot(0.0));
    captures.captureB(makeSnapshot(6.0));
    const auto stableResult = ComparisonEngine::compare(captures);
    captures.reset();
    test.expect(stableResult.a && stableResult.b,
                "comparison result must remain stable after captures reset");

    if (test.failures == 0)
    {
        std::cout << "AIFRED comparison engine: PASS\n";
        return EXIT_SUCCESS;
    }

    std::cerr << "AIFRED comparison engine: " << test.failures << " failure(s)\n";
    return EXIT_FAILURE;
}
