#include "CaptureComparison.h"

#include <algorithm>
#include <cmath>
#include <utility>

namespace aifred::analysis
{
namespace
{
ComparisonAvailability snapshotAvailability(
    const std::shared_ptr<const ViewSnapshot>& a,
    const std::shared_ptr<const ViewSnapshot>& b) noexcept
{
    if (! a && ! b)
        return ComparisonAvailability::missingBothSnapshots;
    if (! a)
        return ComparisonAvailability::missingSnapshotA;
    if (! b)
        return ComparisonAvailability::missingSnapshotB;
    if(a->observation.profileId!=b->observation.profileId || a->observation.profileVersion!=b->observation.profileVersion || a->observation.sampleRate!=b->observation.sampleRate)
        return ComparisonAvailability::incompatibleProfile;
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

    if ((! a->valid || !std::isfinite(a->value)) && (! b->valid || !std::isfinite(b->value)))
        comparison.availability = ComparisonAvailability::bothValuesInvalid;
    else if (! a->valid || !std::isfinite(a->value))
        comparison.availability = ComparisonAvailability::valueAInvalid;
    else if (! b->valid || !std::isfinite(b->value))
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

SpectrumComparison compareSpectrum(const ViewSnapshot* a,
                                   const ViewSnapshot* b,
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

void SnapshotCaptureModel::captureA(const ViewSnapshot& snapshot)
{
    // Capture is a user/UI action, never realtime processing. Allocation here
    // keeps ownership out of DSP producer and preserves a frozen copy.
    a_ = std::make_shared<const ViewSnapshot>(snapshot);
}

void SnapshotCaptureModel::captureB(const ViewSnapshot& snapshot)
{
    b_ = std::make_shared<const ViewSnapshot>(snapshot);
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

const std::shared_ptr<const ViewSnapshot>& SnapshotCaptureModel::a() const noexcept
{
    return a_;
}

const std::shared_ptr<const ViewSnapshot>& SnapshotCaptureModel::b() const noexcept
{
    return b_;
}

SnapshotComparison CaptureComparison::compare(const SnapshotCaptureModel& captures) noexcept
{
    return compare(captures.a(), captures.b());
}

SnapshotComparison CaptureComparison::compare(
    const ViewSnapshot& a,
    const ViewSnapshot& b)
{
    return compare(std::make_shared<const ViewSnapshot>(a),
                   std::make_shared<const ViewSnapshot>(b));
}

SnapshotComparison CaptureComparison::compare(
    const std::shared_ptr<const ViewSnapshot>& a,
    const std::shared_ptr<const ViewSnapshot>& b) noexcept
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

    comparison.samplePeakDbfs = metric(&ViewSnapshot::samplePeakDbfs);
    comparison.rmsDbfs = metric(&ViewSnapshot::rmsDbfs);
    comparison.crestDb = metric(&ViewSnapshot::crestDb);
    comparison.shortTermLufs = metric(&ViewSnapshot::shortTermLufs);
    comparison.width = metric(&ViewSnapshot::width);
    comparison.correlation = metric(&ViewSnapshot::correlation);
    comparison.spectrum = compareSpectrum(snapshotA, snapshotB, comparison.availability);
    return comparison;
}
} // namespace aifred::analysis
