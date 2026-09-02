#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include "PluginProcessor.h"
#include "core/analysis/AnalysisSnapshot.h"

#include <array>
#include <cstdint>

class AifredAudioProcessorEditor final : public juce::AudioProcessorEditor,
                                         private juce::Timer
{
public:
    explicit AifredAudioProcessorEditor(AifredAudioProcessor&);
    ~AifredAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;

private:
    struct DisplayMetric
    {
        float current = 0.0f;
        float target = 0.0f;
        bool valid = false;

        void setTarget(const aifred::analysis::MetricValue& value) noexcept;
        void clear() noexcept;
        bool advance(float amount) noexcept;
    };

    void timerCallback() override;
    void acceptSnapshot(const aifred::analysis::AnalysisSnapshot&);
    void clearDisplay() noexcept;

    void drawHeader(juce::Graphics&, juce::Rectangle<float>) const;
    void drawMeterWorkspace(juce::Graphics&, juce::Rectangle<float>) const;
    void drawLevelCard(juce::Graphics&, juce::Rectangle<float>) const;
    void drawSingleMeterCard(juce::Graphics&, juce::Rectangle<float>,
                             juce::StringRef title, juce::StringRef caption,
                             const DisplayMetric&, float minimum, float maximum,
                             juce::StringRef unit, int decimals,
                             juce::Colour accent) const;
    void drawStereoCard(juce::Graphics&, juce::Rectangle<float>) const;
    void drawSpectrum(juce::Graphics&, juce::Rectangle<float>) const;
    void drawFindingPanel(juce::Graphics&, juce::Rectangle<float>) const;

    void drawPanel(juce::Graphics&, juce::Rectangle<float>) const;
    void drawArc(juce::Graphics&, juce::Rectangle<float>, float normalized,
                 juce::Colour accent, float thickness) const;
    void drawMetricValue(juce::Graphics&, juce::Rectangle<float>,
                         const DisplayMetric&, juce::StringRef unit,
                         int decimals, juce::Colour colour) const;

    [[nodiscard]] juce::String currentFinding() const;
    [[nodiscard]] static float normalized(float value, float minimum, float maximum) noexcept;
    [[nodiscard]] static juce::String formattedValue(const DisplayMetric&, juce::StringRef unit,
                                                     int decimals, bool showPlus = false);

    AifredAudioProcessor& processor;
    juce::TextButton resetButton { "RESET" };

    aifred::analysis::AnalysisSnapshot latestSnapshot {};
    std::uint64_t lastSequence = 0;
    bool hasReceivedSnapshot = false;

    DisplayMetric peak;
    DisplayMetric rms;
    DisplayMetric crest;
    DisplayMetric loudness;
    DisplayMetric width;
    DisplayMetric correlation;
    std::array<DisplayMetric, 7> spectrum;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AifredAudioProcessorEditor)
};
