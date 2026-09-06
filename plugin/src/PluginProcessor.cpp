#include "PluginProcessor.h"
#include "PluginEditor.h"

#include <algorithm>
#include <array>
#include <cmath>

AifredAudioProcessor::AifredAudioProcessor()
    : AudioProcessor (BusesProperties()
                          .withInput ("Input", juce::AudioChannelSet::stereo(), true)
                          .withOutput ("Output", juce::AudioChannelSet::stereo(), true))
{
}

void AifredAudioProcessor::prepareToPlay (double sampleRate, int maximumExpectedSamplesPerBlock)
{
    const auto validSampleRate = sampleRate > 0.0 && std::isfinite (sampleRate);
    juce::ignoreUnused(maximumExpectedSamplesPerBlock);
    const auto channelCount = std::min (2, getTotalNumInputChannels());

    if (! validSampleRate || channelCount <= 0)
    {
        currentSampleRate.store (0.0, std::memory_order_release);
        pipeline_.reset();
        return;
    }

    currentSampleRate.store (sampleRate, std::memory_order_release);
    pipeline_.prepare (sampleRate, channelCount);
}

void AifredAudioProcessor::releaseResources()
{
    // Preserve the most recent useful snapshot when a host stops or suspends audio.
}

bool AifredAudioProcessor::isBusesLayoutSupported (const BusesLayout& layouts) const
{
    const auto input = layouts.getMainInputChannelSet();
    const auto output = layouts.getMainOutputChannelSet();
    const auto isSupportedChannelCount = input == juce::AudioChannelSet::mono()
                                      || input == juce::AudioChannelSet::stereo();

    return isSupportedChannelCount && output == input;
}

void AifredAudioProcessor::processBlock (juce::AudioBuffer<float>& buffer,
                                         juce::MidiBuffer& midiMessages)
{
    juce::ignoreUnused (midiMessages);
    juce::ScopedNoDenormals noDenormals;

    const auto numSamples = buffer.getNumSamples();
    const auto numBufferChannels = buffer.getNumChannels();
    const auto numInputChannels = std::min (getTotalNumInputChannels(), numBufferChannels);
    const auto numOutputChannels = std::min (getTotalNumOutputChannels(), numBufferChannels);

    for (auto channel = numInputChannels; channel < numOutputChannels; ++channel)
        buffer.clear (channel, 0, numSamples);

    if (numSamples <= 0 || numInputChannels <= 0)
        return;

    const auto channelsToAnalyse = std::min (numInputChannels, 2);
    std::array<const float*, 2> channelData { nullptr, nullptr };

    for (auto channel = 0; channel < channelsToAnalyse; ++channel)
    {
        channelData[static_cast<std::size_t> (channel)] = buffer.getReadPointer (channel);
        if (channelData[static_cast<std::size_t> (channel)] == nullptr)
            return;
    }

    // Reject non-finite host data before it can contaminate persistent analyzer state.
    // Floating-point audio above 0 dBFS is valid and is deliberately not clipped.
    for (auto channel = 0; channel < channelsToAnalyse; ++channel)
    {
        const auto* samples = channelData[static_cast<std::size_t> (channel)];
        for (auto sample = 0; sample < numSamples; ++sample)
            if (! std::isfinite (samples[sample]))
                return;
    }

    bool known=false,playing=false;std::int64_t position=-1;
    if(auto* playhead=getPlayHead()) if(auto info=playhead->getPosition()) {known=true;playing=info->getIsPlaying();if(auto time=info->getTimeInSamples())position=*time;}
    pipeline_.process(channelData.data(),channelsToAnalyse,numSamples,known,playing,position);
}

juce::AudioProcessorEditor* AifredAudioProcessor::createEditor()
{
    return new AifredAudioProcessorEditor (*this);
}

bool AifredAudioProcessor::hasEditor() const
{
    return true;
}

const juce::String AifredAudioProcessor::getName() const
{
    return JucePlugin_Name;
}

bool AifredAudioProcessor::acceptsMidi() const
{
    return false;
}

bool AifredAudioProcessor::producesMidi() const
{
    return false;
}

bool AifredAudioProcessor::isMidiEffect() const
{
    return false;
}

double AifredAudioProcessor::getTailLengthSeconds() const
{
    return 0.0;
}

int AifredAudioProcessor::getNumPrograms()
{
    return 1;
}

int AifredAudioProcessor::getCurrentProgram()
{
    return 0;
}

void AifredAudioProcessor::setCurrentProgram (int index)
{
    juce::ignoreUnused (index);
}

const juce::String AifredAudioProcessor::getProgramName (int index)
{
    juce::ignoreUnused (index);
    return {};
}

void AifredAudioProcessor::changeProgramName (int index, const juce::String& newName)
{
    juce::ignoreUnused (index, newName);
}

void AifredAudioProcessor::getStateInformation (juce::MemoryBlock& destData)
{
    juce::XmlElement state("AIFRED_OFFICIAL_STATE");
    state.setAttribute("version",2);
    state.setAttribute("dsp_profile",juce::String(aifred::core::profile(pipeline_.selectedProfile()).name.data()));
    state.setAttribute("spectrum_display_range",juce::String(aifred::core::spectrumRangeName(pipeline_.presentation().spectrumRange).data()));
    state.setAttribute("presentation_customized",pipeline_.presentationCustomized());
    copyXmlToBinary(state,destData);
}

void AifredAudioProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    if(auto state=getXmlFromBinary(data,sizeInBytes))
        if(state->hasTagName("AIFRED_OFFICIAL_STATE"))
        {
            pipeline_.setProfile(aifred::core::profileFromName(state->getStringAttribute("dsp_profile").toStdString()));
            if(state->hasAttribute("spectrum_display_range"))
                pipeline_.restorePresentation(aifred::core::spectrumRangeFromName(state->getStringAttribute("spectrum_display_range").toStdString()),
                                              state->getBoolAttribute("presentation_customized",false));
            else
                pipeline_.restorePresentation(aifred::core::profile(pipeline_.selectedProfile()).presentation.spectrumRange,false);
        }
}

aifred::analysis::ViewSnapshot AifredAudioProcessor::getViewSnapshot() const noexcept
{
    return aifred::analysis::makeView(pipeline_.live(),pipeline_.observation(),pipeline_.presentation());
}

double AifredAudioProcessor::getCurrentSampleRate() const noexcept
{
    return currentSampleRate.load (std::memory_order_acquire);
}

void AifredAudioProcessor::resetAnalysis() noexcept
{
    pipeline_.reset();
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new AifredAudioProcessor();
}
