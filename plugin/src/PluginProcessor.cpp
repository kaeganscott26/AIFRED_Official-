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
    const auto safeMaximumBlockSize = std::max (1, maximumExpectedSamplesPerBlock);
    const auto channelCount = std::min (2, getTotalNumInputChannels());

    if (! validSampleRate || channelCount <= 0)
    {
        currentSampleRate.store (0.0, std::memory_order_release);
        analysisCoordinator.reset();
        return;
    }

    currentSampleRate.store (sampleRate, std::memory_order_release);
    analysisCoordinator.prepare (sampleRate, safeMaximumBlockSize, channelCount);
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

    analysisCoordinator.process (channelData.data(), channelsToAnalyse, numSamples);
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
    destData.reset();
}

void AifredAudioProcessor::setStateInformation (const void* data, int sizeInBytes)
{
    juce::ignoreUnused (data, sizeInBytes);
}

aifred::analysis::AnalysisSnapshot AifredAudioProcessor::getAnalysisSnapshot() const noexcept
{
    return analysisCoordinator.getSnapshot();
}

double AifredAudioProcessor::getCurrentSampleRate() const noexcept
{
    return currentSampleRate.load (std::memory_order_acquire);
}

void AifredAudioProcessor::resetAnalysis() noexcept
{
    analysisCoordinator.reset();
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new AifredAudioProcessor();
}
