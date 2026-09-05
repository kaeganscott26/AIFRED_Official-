#pragma once
#include "aifred/IntelligenceClient.h"

#include <atomic>

#include <juce_audio_processors/juce_audio_processors.h>

#include "aifred/Pipeline.h"
#include "ViewSnapshot.h"

class AifredAudioProcessor final : public juce::AudioProcessor
{
public:
    AifredAudioProcessor();
    ~AifredAudioProcessor() override = default;

    void prepareToPlay (double sampleRate, int maximumExpectedSamplesPerBlock) override;
    void releaseResources() override;
    bool isBusesLayoutSupported (const BusesLayout& layouts) const override;
    void processBlock (juce::AudioBuffer<float>& buffer, juce::MidiBuffer& midiMessages) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;

    const juce::String getName() const override;
    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram (int index) override;
    const juce::String getProgramName (int index) override;
    void changeProgramName (int index, const juce::String& newName) override;

    void getStateInformation (juce::MemoryBlock& destData) override;
    void setStateInformation (const void* data, int sizeInBytes) override;

    [[nodiscard]] aifred::analysis::ViewSnapshot getViewSnapshot() const noexcept;
    [[nodiscard]] double getCurrentSampleRate() const noexcept;
    void resetAnalysis() noexcept;
    aifred::core::Pipeline& pipeline() noexcept { return pipeline_; }

    aifred::core::IntelligenceClient& intelligence() noexcept {return intelligence_;}

private:
    aifred::core::IntelligenceClient intelligence_ { "official" };
    aifred::core::Pipeline pipeline_ { "official", "4.0.0-alpha.2" };
    std::atomic<double> currentSampleRate { 0.0 };

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (AifredAudioProcessor)
};

