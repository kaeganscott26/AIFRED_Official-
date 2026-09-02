#pragma once

#include "AnalysisSnapshot.h"

#include <array>
#include <memory>

namespace aifred::analysis
{
// Deltas always mean B minus A. The availability value keeps a missing capture,
// an unavailable measurement, and an incompatible spectrum grid distinguishable.
enum class ComparisonAvailability
{
    available,
    missingBothSnapshots,
    missingSnapshotA,
    missingSnapshotB,
    bothValuesInvalid,
    valueAInvalid,
    valueBInvalid,
    incompatibleSpectrumGrid
};

struct MetricComparison
{
    MetricValue a;
    MetricValue b;
    MetricValue delta;
    ComparisonAvailability availability = ComparisonAvailability::missingBothSnapshots;
};

struct SpectrumComparison
{
    MetricComparison binWidthHz;
    // Raw bin values remain in SnapshotComparison::a/b. Keeping only the
    // validity-aware deltas here avoids copying three full FFT arrays.
    std::array<MetricValue, AnalysisSnapshot::spectrumBinCount> deltaBins {};
    ComparisonAvailability availability = ComparisonAvailability::missingBothSnapshots;
};

struct SnapshotComparison
{
    // Shared ownership of immutable copies keeps a result stable even if the
    // capture model is subsequently replaced or reset.
    std::shared_ptr<const AnalysisSnapshot> a;
    std::shared_ptr<const AnalysisSnapshot> b;
    ComparisonAvailability availability = ComparisonAvailability::missingBothSnapshots;

    MetricComparison samplePeakDbfs;
    MetricComparison rmsDbfs;
    MetricComparison crestDb;
    MetricComparison shortTermLufs;
    MetricComparison width;
    MetricComparison correlation;
    SpectrumComparison spectrum;

    [[nodiscard]] bool ready() const noexcept
    {
        return availability == ComparisonAvailability::available;
    }
};

// Owns frozen copies of two snapshots. Captures change only through an explicit
// capture, reset, or swap call; the live AnalysisCoordinator is never referenced.
class SnapshotCaptureModel
{
public:
    void captureA(const AnalysisSnapshot& snapshot);
    void captureB(const AnalysisSnapshot& snapshot);
    void resetA() noexcept;
    void resetB() noexcept;
    void reset() noexcept;
    void swap() noexcept;

    [[nodiscard]] bool hasA() const noexcept;
    [[nodiscard]] bool hasB() const noexcept;
    [[nodiscard]] const std::shared_ptr<const AnalysisSnapshot>& a() const noexcept;
    [[nodiscard]] const std::shared_ptr<const AnalysisSnapshot>& b() const noexcept;

private:
    std::shared_ptr<const AnalysisSnapshot> a_;
    std::shared_ptr<const AnalysisSnapshot> b_;
};

class ComparisonEngine
{
public:
    [[nodiscard]] static SnapshotComparison compare(
        const SnapshotCaptureModel& captures) noexcept;
    [[nodiscard]] static SnapshotComparison compare(
        const std::shared_ptr<const AnalysisSnapshot>& a,
        const std::shared_ptr<const AnalysisSnapshot>& b) noexcept;
    [[nodiscard]] static SnapshotComparison compare(
        const AnalysisSnapshot& a,
        const AnalysisSnapshot& b);
};
} // namespace aifred::analysis
