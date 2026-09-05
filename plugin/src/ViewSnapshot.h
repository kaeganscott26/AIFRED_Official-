#pragma once
#include "aifred/Filter.h"

namespace aifred::analysis
{
using MetricValue = core::MetricValue;
// Frontend projection only. Engineering values are observed; hero bins remain
// precise measured power. This object is never serialized to a model request.
struct ViewSnapshot
{
    static constexpr std::size_t spectrumBinCount=core::maximumBins;
    static constexpr std::size_t spectrumBandCount=30;
    std::uint64_t sequence=0,audioSampleClock=0,sampleClipCount=0;
    double elapsedSeconds=0;
    bool hasSignal=false,sampleClipActive=false;
    MetricValue samplePeakDbfs,maxSampleOverDb,rmsDbfs,crestDb,shortTermLufs,width,correlation,spectrumBinWidthHz;
    std::array<MetricValue,spectrumBinCount> spectrumBins {};
    std::array<MetricValue,spectrumBandCount> spectrumBands {};
    core::ObservationSnapshot observation;
};
inline ViewSnapshot makeView(const core::EngineSnapshot& live,const core::ObservationSnapshot& observed)
{
    ViewSnapshot v;v.observation=observed;v.sequence=live.sequence;v.audioSampleClock=live.sampleEnd;
    v.elapsedSeconds=observed.durationSeconds;v.hasSignal=observed.signalActive;v.sampleClipActive=live.sampleClipActive;v.sampleClipCount=live.sampleClipCount;
    const auto metric=[&](core::MetricId id){const auto& m=observed.get(id);return MetricValue{core::Filter::published(m.typical,core::metricDefinitions[core::index(id)].decimals),m.valid};};
    v.samplePeakDbfs=metric(core::MetricId::samplePeak);v.rmsDbfs=metric(core::MetricId::rms);v.crestDb=metric(core::MetricId::crest);v.shortTermLufs=metric(core::MetricId::shortTerm);
    v.width=metric(core::MetricId::width);v.width.value/=100;v.correlation=metric(core::MetricId::correlation);
    v.maxSampleOverDb={std::max(0.0,live.get(core::MetricId::samplePeak).value),live.get(core::MetricId::samplePeak).valid};
    v.spectrumBinWidthHz={live.binWidthHz,live.binCount>0};
    for(std::size_t i=0;i<live.binCount;++i)v.spectrumBins[i]=core::powerDb(live.averagePower[i]);
    for(std::size_t i=0;i<30;++i)v.spectrumBands[i]={core::Filter::published(observed.bands[i].typical,0),observed.bands[i].valid};
    return v;
}
}
