#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>
#if JUCE_WEB_BROWSER
#include <juce_gui_extra/juce_gui_extra.h>
#endif

#include "PluginProcessor.h"


#include "ReferenceClient.h"
#include "ViewSnapshot.h"
#include "CaptureComparison.h"

#include <array>
#include <cstdint>
#include <memory>

class AifredAudioProcessorEditor final : public juce::AudioProcessorEditor,
                                         private juce::Timer
{
public:
    explicit AifredAudioProcessorEditor(AifredAudioProcessor&);
    ~AifredAudioProcessorEditor() override;
    void paint(juce::Graphics&) override;
    void resized() override;

private:
    enum class Mode { analyze, compare, reference, history };

    struct DisplayMetric
    {
        float current = 0.0f;
        float target = 0.0f;
        bool valid = false;
        void setTarget(const aifred::analysis::MetricValue&) noexcept;
        void clear() noexcept;
        bool advance(float amount) noexcept;
    };

    struct VisualizationState
    {
        float normalizedPeak = 0.0f;
        float normalizedRms = 0.0f;
        float normalizedCrest = 0.0f;
        float normalizedLoudness = 0.0f;
        float width = 0.0f;
        float correlation = 0.0f;
        bool signalActive = false;
        double elapsedSeconds = 0.0;
        double spectrumBinWidthHz = 0.0;
        float spectrumFloorDb = -96.0f;
        float spectrumCeilingDb = 0.0f;
        bool fillSpectrum = true;
        bool showPeakTrace = false;
        std::array<float, aifred::analysis::ViewSnapshot::spectrumBinCount> spectrumBins {};
        std::array<bool, aifred::analysis::ViewSnapshot::spectrumBinCount> spectrumValid {};
        std::array<float, aifred::analysis::ViewSnapshot::spectrumBinCount> peakSpectrumBins {};
        std::array<bool, aifred::analysis::ViewSnapshot::spectrumBinCount> peakSpectrumValid {};
    };

    void timerCallback() override;
    void acceptSnapshot(const aifred::analysis::ViewSnapshot&);
    void clearDisplay() noexcept;
    void selectMode(Mode);
    void updateModeButtons();
    void updateCompareButtons();
    void updateReferenceUi();
    void updateChatUi();
    void sendChatQuestion();
    void appendConversationLine(juce::StringRef speaker, const juce::String& text);
    [[nodiscard]] const aifred::services::ReferenceProfile* selectedReference() const noexcept;


    void drawHeader(juce::Graphics&, juce::Rectangle<float>) const;
    void drawModeNavigation(juce::Graphics&, juce::Rectangle<float>) const;
    void drawAnalyzeMode(juce::Graphics&, juce::Rectangle<float>) const;
    void drawCompareMode(juce::Graphics&, juce::Rectangle<float>) const;
    void drawReferenceMode(juce::Graphics&, juce::Rectangle<float>) const;
    void drawReferenceMetrics(juce::Graphics&, juce::Rectangle<float>,
                              const aifred::services::ReferenceProfile*) const;
    void drawChatPanel(juce::Graphics&, juce::Rectangle<float>) const;
    void drawUnavailableMode(juce::Graphics&, juce::Rectangle<float>,
                             juce::StringRef title, juce::StringRef detail) const;
    void drawSpectrumHero(juce::Graphics&, juce::Rectangle<float>) const;
    void drawSnapshotSpectrum(juce::Graphics&, juce::Rectangle<float>,
                              const aifred::analysis::ViewSnapshot*,
                              juce::StringRef label) const;
    void drawSupportMeters(juce::Graphics&, juce::Rectangle<float>) const;
    void drawLevelCard(juce::Graphics&, juce::Rectangle<float>) const;
    void drawSingleMeterCard(juce::Graphics&, juce::Rectangle<float>, juce::StringRef title,
                             juce::StringRef caption, const DisplayMetric&, float minimum,
                             float maximum, juce::StringRef unit, int decimals,
                             juce::Colour accent) const;
    void drawStereoCard(juce::Graphics&, juce::Rectangle<float>) const;
    void drawPanel(juce::Graphics&, juce::Rectangle<float>, float corner = 10.0f) const;
    void drawArc(juce::Graphics&, juce::Rectangle<float>, float normalized,
                 juce::Colour accent, float thickness) const;
    void drawMetricValue(juce::Graphics&, juce::Rectangle<float>, const DisplayMetric&,
                         juce::StringRef unit, int decimals, juce::Colour colour) const;

    [[nodiscard]] VisualizationState makeVisualizationState() const noexcept;
    void publishVisualizationState();
    void initialiseWebVisualizer();
    void layoutWebVisualizer(juce::Rectangle<int> heroBounds);
    [[nodiscard]] static float normalized(float value, float minimum, float maximum) noexcept;
    [[nodiscard]] static juce::String formattedValue(const DisplayMetric&, juce::StringRef unit,
                                                     int decimals, bool showPlus = false);

    AifredAudioProcessor& processor;
    Mode activeMode = Mode::analyze;
    aifred::analysis::SnapshotCaptureModel captures;

    juce::TextButton analyzeButton { "ANALYZE" };
    juce::TextButton compareButton { "COMPARE" };
    juce::TextButton referenceButton { "REFERENCE" };
    juce::TextButton historyButton { "HISTORY" };
    juce::TextButton resetButton { "RESET" };
    juce::TextButton captureAButton { "CAPTURE A" };
    juce::TextButton captureBButton { "CAPTURE B" };
    juce::TextButton resetAButton { "RESET A" };
    juce::TextButton resetBButton { "RESET B" };
    juce::TextButton swapButton { "SWAP A/B" };
    juce::TextButton refreshReferencesButton { "REFRESH" };
    juce::ComboBox referenceSelector;
    juce::ComboBox profileSelector;
    juce::ComboBox displayRangeSelector;
    juce::TextButton chatToggleButton { "ASK AIFRED" };
    juce::TextButton sendButton { "SEND" };
    juce::TextButton retryButton { "RETRY" };
    juce::TextEditor chatHistory;
    juce::TextEditor chatInput;

    aifred::analysis::ViewSnapshot latestSnapshot {};
    std::uint64_t lastSequence = 0;
    bool hasReceivedSnapshot = false;
    DisplayMetric peak, rms, crest, loudness, width, correlation, spectrumBinWidthHz;
    std::array<DisplayMetric, aifred::analysis::ViewSnapshot::spectrumBinCount> spectrumBins;
    std::array<DisplayMetric, aifred::analysis::ViewSnapshot::spectrumBinCount> peakSpectrumBins;

    aifred::services::ReferenceCatalog referenceCatalog;
    std::uint64_t lastReferenceRevision = 0;
    std::uint64_t lastHealthRevision = 0;
    std::uint64_t lastChatRevision = 0;
    int healthRefreshCounter = 0;
    bool chatOpen = false;
    juce::String lastQuestion;

#if JUCE_WEB_BROWSER
    std::unique_ptr<juce::WebBrowserComponent> webVisualizer;
    bool webVisualizerReady = false;
#endif

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AifredAudioProcessorEditor)
};
