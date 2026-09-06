#pragma once
#include "aifred/Filter.h"

namespace aifred::analysis
{
using MetricValue = core::MetricValue;
struct MetricDetail
{
    core::MetricId id=core::MetricId::samplePeak;
    std::string_view displayName,unit;
    bool valid=false,isLive=false;
    double rawCurrent=0,displayedValue=0;
    core::MetricObservation observed;
    core::ProfileId activeProfile=core::ProfileId::mixBalanced,emphasizedBy=core::ProfileId::mixBalanced;
    std::uint32_t profileRevision=1;
};
// Frontend projection only. Engineering values are observed; hero bins remain
// precise measured power. This object is never serialized to a model request.
struct ViewSnapshot
{
    static constexpr std::size_t spectrumBinCount=core::maximumBins;
    static constexpr std::size_t spectrumBandCount=30;
    std::uint64_t sequence=0,audioSampleClock=0,sampleClipCount=0;
    double elapsedSeconds=0;
    bool hasSignal=false,sampleClipActive=false;
    core::ProfileId activeProfile=core::ProfileId::mixBalanced;
    std::uint32_t profileRevision=1;
    std::string_view measurementConfigurationId="MIX_BALANCED.r1";
    core::PresentationConfiguration presentation=core::standardPresentation;
    MetricValue samplePeakDbfs,maxSampleOverDb,rmsDbfs,crestDb,shortTermLufs,width,correlation,spectrumBinWidthHz;
    std::array<MetricValue,spectrumBinCount> spectrumBins {};
    std::array<MetricValue,spectrumBinCount> peakSpectrumBins {};
    std::array<MetricValue,spectrumBandCount> spectrumBands {};
    std::array<MetricDetail,core::metricCount> metricDetails {};
    core::ObservationSnapshot observation;
};
inline ViewSnapshot makeView(const core::EngineSnapshot& live,const core::ObservationSnapshot& observed,
                             core::PresentationConfiguration presentation=core::standardPresentation)
{
    ViewSnapshot v;v.observation=observed;v.sequence=live.sequence;v.audioSampleClock=live.sampleEnd;
    v.activeProfile=live.profileId;v.profileRevision=live.profileVersion;v.measurementConfigurationId=core::profile(live.profileId).identity;v.presentation=presentation;
    v.elapsedSeconds=observed.durationSeconds;v.hasSignal=observed.signalActive;v.sampleClipActive=live.sampleClipActive;v.sampleClipCount=live.sampleClipCount;
    const auto metric=[&](core::MetricId id){const auto& m=observed.get(id);return MetricValue{m.typical,m.valid};};
    v.samplePeakDbfs=metric(core::MetricId::samplePeak);v.rmsDbfs=metric(core::MetricId::rms);v.crestDb=metric(core::MetricId::crest);v.shortTermLufs=metric(core::MetricId::shortTerm);
    v.width=live.get(core::MetricId::width);v.width.value/=100;v.correlation=live.get(core::MetricId::correlation);
    v.maxSampleOverDb={std::max(0.0,live.get(core::MetricId::samplePeak).value),live.get(core::MetricId::samplePeak).valid};
    v.spectrumBinWidthHz={live.binWidthHz,live.binCount>0};
    for(std::size_t i=0;i<live.binCount;++i){v.spectrumBins[i]=core::powerDb(live.averagePower[i]);v.peakSpectrumBins[i]=core::powerDb(live.peakPower[i]);}
    for(std::size_t i=0;i<30;++i)v.spectrumBands[i]={observed.bands[i].typical,observed.bands[i].valid};
    for(std::size_t i=0;i<core::metricCount;++i)
    {
        auto& detail=v.metricDetails[i];const auto id=static_cast<core::MetricId>(i);const auto& definition=core::metricDefinitions[i];
        detail.id=id;detail.displayName=definition.displayName;detail.unit=definition.unit;detail.isLive=definition.source==core::MetricSource::live;
        detail.rawCurrent=live.metrics[i].value;detail.observed=observed.metrics[i];detail.activeProfile=live.profileId;
        detail.profileRevision=live.profileVersion;detail.emphasizedBy=definition.emphasizedBy;
        const auto shown=detail.isLive?live.metrics[i]:core::MetricValue{detail.observed.typical,detail.observed.valid};
        detail.valid=shown.valid;detail.displayedValue=shown.value;
    }
    return v;
}
}
