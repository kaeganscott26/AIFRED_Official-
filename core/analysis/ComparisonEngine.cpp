#include "ComparisonEngine.h"

#include <algorithm>
#include <cmath>
#include <utility>

namespace aifred::analysis
{
namespace
{
ComparisonAvailability snapshotAvailability(
    const std::shared_ptr<const AnalysisSnapshot>& a,
    const std::shared_ptr<const AnalysisSnapshot>& b) noexcept
{
    if (! a && ! b)
        return ComparisonAvailability::missingBothSnapshots;
    if (! a)
        return ComparisonAvailability::missingSnapshotA;
    if (! b)
        return ComparisonAvailability::missingSnapshotB;
    return ComparisonAvailability::available;
}

MetricComparison compareMetric(const MetricValue* a,
                               const MetricValue* b,
                               const ComparisonAvailability captureAvailability) noexcept
{
    MetricComparison comparison;
    if (a != nullptr)
        comparison.a = *a;
    if (b != nullptr)
        comparison.b = *b;

    if (captureAvailability != ComparisonAvailability::available)
    {
        comparison.availability = captureAvailability;
        return comparison;
    }

    if (! a->valid && ! b->valid)
        comparison.availability = ComparisonAvailability::bothValuesInvalid;
    else if (! a->valid)
        comparison.availability = ComparisonAvailability::valueAInvalid;
    else if (! b->valid)
        comparison.availability = ComparisonAvailability::valueBInvalid;
    else
    {
        comparison.delta = { b->value - a->value, true };
        comparison.availability = ComparisonAvailability::available;
    }

    return comparison;
}

bool sameSpectrumGrid(const MetricValue& a, const MetricValue& b) noexcept
{
    if (! a.valid || ! b.valid)
        return false;

    const auto scale = std::max({ 1.0, std::abs(a.value), std::abs(b.value) });
    return std::abs(a.value - b.value) <= scale * 1.0e-9;
}

SpectrumComparison compareSpectrum(const AnalysisSnapshot* a,
                                   const AnalysisSnapshot* b,
                                   const ComparisonAvailability captureAvailability) noexcept
{
    SpectrumComparison spectrum;
    const auto* widthA = a != nullptr ? &a->spectrumBinWidthHz : nullptr;
    const auto* widthB = b != nullptr ? &b->spectrumBinWidthHz : nullptr;
    spectrum.binWidthHz = compareMetric(widthA, widthB, captureAvailability);

    if (captureAvailability != ComparisonAvailability::available)
    {
        spectrum.availability = captureAvailability;
        return spectrum;
    }

    if (spectrum.binWidthHz.availability != ComparisonAvailability::available)
    {
        spectrum.availability = spectrum.binWidthHz.availability;
        return spectrum;
    }

    if (! sameSpectrumGrid(a->spectrumBinWidthHz, b->spectrumBinWidthHz))
    {
        spectrum.availability = ComparisonAvailability::incompatibleSpectrumGrid;
        return spectrum;
    }

    spectrum.availability = ComparisonAvailability::available;
    for (std::size_t bin = 0; bin < spectrum.deltaBins.size(); ++bin)
    {
        const auto& binA = a->spectrumBins[bin];
        const auto& binB = b->spectrumBins[bin];
        if (binA.valid && binB.valid)
            spectrum.deltaBins[bin] = { binB.value - binA.value, true };
    }
    return spectrum;
}
} // namespace

void SnapshotCaptureModel::captureA(const AnalysisSnapshot& snapshot)
{
    // Capture is a user/UI action, never realtime processing. Allocation here
    // keeps ownership out of AnalysisCoordinator and preserves a frozen copy.
    a_ = std::make_shared<const AnalysisSnapshot>(snapshot);
}

void SnapshotCaptureModel::captureB(const AnalysisSnapshot& snapshot)
{
    b_ = std::make_shared<const AnalysisSnapshot>(snapshot);
}

void SnapshotCaptureModel::resetA() noexcept
{
    a_.reset();
}

void SnapshotCaptureModel::resetB() noexcept
{
    b_.reset();
}

void SnapshotCaptureModel::reset() noexcept
{
    a_.reset();
    b_.reset();
}

void SnapshotCaptureModel::swap() noexcept
{
    std::swap(a_, b_);
}

bool SnapshotCaptureModel::hasA() const noexcept
{
    return static_cast<bool>(a_);
}

bool SnapshotCaptureModel::hasB() const noexcept
{
    return static_cast<bool>(b_);
}

const std::shared_ptr<const AnalysisSnapshot>& SnapshotCaptureModel::a() const noexcept
{
    return a_;
}

const std::shared_ptr<const AnalysisSnapshot>& SnapshotCaptureModel::b() const noexcept
{
    return b_;
}

SnapshotComparison ComparisonEngine::compare(const SnapshotCaptureModel& captures) noexcept
{
    return compare(captures.a(), captures.b());
}

SnapshotComparison ComparisonEngine::compare(
    const AnalysisSnapshot& a,
    const AnalysisSnapshot& b)
{
    return compare(std::make_shared<const AnalysisSnapshot>(a),
                   std::make_shared<const AnalysisSnapshot>(b));
}

SnapshotComparison ComparisonEngine::compare(
    const std::shared_ptr<const AnalysisSnapshot>& a,
    const std::shared_ptr<const AnalysisSnapshot>& b) noexcept
{
    SnapshotComparison comparison;
    comparison.a = a;
    comparison.b = b;
    comparison.availability = snapshotAvailability(a, b);

    const auto* snapshotA = a.get();
    const auto* snapshotB = b.get();

    const auto metric = [snapshotA, snapshotB, &comparison](const auto member)
    {
        const auto* valueA = snapshotA != nullptr ? &(snapshotA->*member) : nullptr;
        const auto* valueB = snapshotB != nullptr ? &(snapshotB->*member) : nullptr;
        return compareMetric(valueA, valueB, comparison.availability);
    };

    comparison.samplePeakDbfs = metric(&AnalysisSnapshot::samplePeakDbfs);
    comparison.rmsDbfs = metric(&AnalysisSnapshot::rmsDbfs);
    comparison.crestDb = metric(&AnalysisSnapshot::crestDb);
    comparison.shortTermLufs = metric(&AnalysisSnapshot::shortTermLufs);
    comparison.width = metric(&AnalysisSnapshot::width);
    comparison.correlation = metric(&AnalysisSnapshot::correlation);
    comparison.spectrum = compareSpectrum(snapshotA, snapshotB, comparison.availability);
    return comparison;
}
} // namespace aifred::analysis
