#include "PluginEditor.h"
#include "core/version/BuildIdentity.h"

#if JUCE_WEB_BROWSER
#include "AifredVisualizationAssets.h"
#endif

#include <algorithm>
#include <cmath>
#include <limits>

namespace
{
constexpr int refreshHz = 60;

constexpr float spectrumSmoothing = 0.34f;
constexpr float spectrumFloorDb = -96.0f;
constexpr float spectrumCeilingDb = 0.0f;
constexpr float minimumFrequencyHz = 20.0f;
constexpr float maximumFrequencyHz = 20000.0f;

const juce::Colour backgroundTop { 0xff09101a };
const juce::Colour backgroundBottom { 0xff030609 };
const juce::Colour panelTop { 0xff121c28 };
const juce::Colour panelBottom { 0xff09111a };
const juce::Colour panelStroke { 0xff263747 };
const juce::Colour textPrimary { 0xffeef8fb };
const juce::Colour textSecondary { 0xff8da5b5 };
const juce::Colour cyan { 0xff4bdcf2 };
const juce::Colour aurora { 0xff60efb3 };
const juce::Colour blue { 0xff729cff };
const juce::Colour danger { 0xffff6e72 };

constexpr std::array<float, 12> frequencyLandmarks {
    20.0f, 40.0f, 80.0f, 160.0f, 315.0f, 630.0f,
    1000.0f, 2000.0f, 4000.0f, 8000.0f, 16000.0f, 20000.0f
};

juce::Font makeFont(float height, juce::Font::FontStyleFlags style = juce::Font::plain)
{
    return juce::Font(juce::FontOptions(height, style));
}

juce::String frequencyLabel(float frequency)
{
    return frequency >= 1000.0f ? juce::String(juce::roundToInt(frequency / 1000.0f)) + "k"
                                : juce::String(juce::roundToInt(frequency));
}

float frequencyToX(float frequency, juce::Rectangle<float> bounds)
{
    const auto proportion = std::log10(frequency / minimumFrequencyHz)
                          / std::log10(maximumFrequencyHz / minimumFrequencyHz);
    return bounds.getX() + bounds.getWidth() * juce::jlimit(0.0f, 1.0f, proportion);
}

juce::String metricText(const aifred::analysis::MetricValue& metric,
                        int decimals, juce::StringRef unit, bool showPlus = false)
{
    if (! metric.valid || ! std::isfinite(metric.value))
        return "--";
    auto value = juce::String(metric.value, decimals);
    if (showPlus && metric.value > 0.0)
        value = "+" + value;
    return unit.isEmpty() ? value : value + " " + unit;
}

juce::String buildIdentityText()
{
    using aifred::build::BuildIdentity;
    const auto text = [] (std::string_view value)
    {
        return juce::String::fromUTF8(value.data(), static_cast<int>(value.size()));
    };
    return text(BuildIdentity::version) + "  /  " + text(BuildIdentity::commit) + "  /  "
         + text(BuildIdentity::platform) + " " + text(BuildIdentity::configuration);
}

#if JUCE_WEB_BROWSER
juce::WebBrowserComponent::Resource makeWebResource(const char* data, int size,
                                                     juce::String mimeType)
{
    juce::WebBrowserComponent::Resource resource;
    const auto* begin = reinterpret_cast<const std::byte*>(data);
    resource.data.assign(begin, begin + size);
    resource.mimeType = std::move(mimeType);
    return resource;
}
#endif
}

AifredAudioProcessorEditor::AifredAudioProcessorEditor(AifredAudioProcessor& owner)
    : AudioProcessorEditor(&owner), processor(owner)
{
    addAndMakeVisible(profileSelector);
    for(std::size_t i=0;i<aifred::core::profiles.size();++i) profileSelector.addItem(juce::String(aifred::core::profiles[i].name.data()),static_cast<int>(i)+1);
    profileSelector.setSelectedId(static_cast<int>(processor.pipeline().selectedProfile())+1,juce::dontSendNotification);
    profileSelector.onChange=[this]{processor.pipeline().setProfile(static_cast<aifred::core::ProfileId>(profileSelector.getSelectedId()-1));};
    setOpaque(true);
    setResizable(true, true);
    setResizeLimits(860, 600, 1760, 1180);
    setSize(1180, 760);

    const auto configure = [this] (juce::TextButton& button)
    {
        button.setColour(juce::TextButton::buttonColourId, juce::Colours::transparentBlack);
        button.setColour(juce::TextButton::buttonOnColourId, cyan.withAlpha(0.14f));
        button.setColour(juce::TextButton::textColourOffId, textSecondary);
        button.setColour(juce::TextButton::textColourOnId, textPrimary);
        button.setMouseCursor(juce::MouseCursor::PointingHandCursor);
        addAndMakeVisible(button);
    };

    for (auto* button : { &analyzeButton, &compareButton, &referenceButton, &historyButton,
                          &resetButton, &captureAButton, &captureBButton, &resetAButton,
                          &resetBButton, &swapButton, &refreshReferencesButton,
                          &chatToggleButton, &sendButton, &retryButton })
        configure(*button);

    referenceSelector.setTextWhenNothingSelected("SELECT REFERENCE");
    referenceSelector.setTextWhenNoChoicesAvailable("NO REFERENCES AVAILABLE");
    referenceSelector.setColour(juce::ComboBox::backgroundColourId, panelBottom);
    referenceSelector.setColour(juce::ComboBox::outlineColourId, panelStroke);
    referenceSelector.setColour(juce::ComboBox::textColourId, textPrimary);
    addAndMakeVisible(referenceSelector);

    chatHistory.setMultiLine(true);
    chatHistory.setReadOnly(true);
    chatHistory.setScrollbarsShown(true);
    chatHistory.setColour(juce::TextEditor::backgroundColourId, backgroundBottom.withAlpha(0.86f));
    chatHistory.setColour(juce::TextEditor::outlineColourId, panelStroke);
    chatHistory.setColour(juce::TextEditor::textColourId, textPrimary);
    chatHistory.setFont(makeFont(12.0f));
    chatHistory.setText("AIFRED: Ask about the measured mix context. I will only receive the facts available in the active mode.\n");
    addAndMakeVisible(chatHistory);

    chatInput.setMultiLine(false);
    chatInput.setTextToShowWhenEmpty("Ask about this mix...", textSecondary);
    chatInput.setColour(juce::TextEditor::backgroundColourId, backgroundBottom);
    chatInput.setColour(juce::TextEditor::outlineColourId, panelStroke);
    chatInput.setColour(juce::TextEditor::focusedOutlineColourId, cyan);
    chatInput.setColour(juce::TextEditor::textColourId, textPrimary);
    chatInput.setFont(makeFont(12.0f));
    addAndMakeVisible(chatInput);

    analyzeButton.onClick = [this] { selectMode(Mode::analyze); };
    compareButton.onClick = [this] { selectMode(Mode::compare); };
    referenceButton.onClick = [this] { selectMode(Mode::reference); };
    historyButton.onClick = [this] { selectMode(Mode::history); };
    captureAButton.onClick = [this] { captures.captureA(latestSnapshot); updateCompareButtons(); repaint(); };
    captureBButton.onClick = [this] { captures.captureB(latestSnapshot); updateCompareButtons(); repaint(); };
    resetAButton.onClick = [this] { captures.resetA(); updateCompareButtons(); repaint(); };
    resetBButton.onClick = [this] { captures.resetB(); updateCompareButtons(); repaint(); };
    swapButton.onClick = [this] { captures.swap(); updateCompareButtons(); repaint(); };
    refreshReferencesButton.onClick = [this]
    {
        aifred::services::ReferenceClient::instance().refreshAsync();
        updateReferenceUi();
    };
    referenceSelector.onChange = [this] { repaint(); };
    chatToggleButton.onClick = [this]
    {
        chatOpen = ! chatOpen;
        chatToggleButton.setButtonText(chatOpen ? "CLOSE CHAT" : "ASK AIFRED");
        resized();
        repaint();
    };
    sendButton.onClick = [this] { sendChatQuestion(); };
    retryButton.onClick = [this]
    {
        if (lastQuestion.isNotEmpty())
        {
            chatInput.setText(lastQuestion, false);
            sendChatQuestion();
        }
    };
    chatInput.onReturnKey = [this] { sendChatQuestion(); };
    resetButton.onClick = [this]
    {
        processor.resetAnalysis();
        clearDisplay();
        hasReceivedSnapshot = false;
        lastSequence = 0;
        repaint();
    };

    updateModeButtons();
    updateCompareButtons();
    updateReferenceUi();
    updateChatUi();
    initialiseWebVisualizer();
    acceptSnapshot(processor.getViewSnapshot());
    processor.intelligence().pingHealthAsync();
    startTimerHz(refreshHz);
}

AifredAudioProcessorEditor::~AifredAudioProcessorEditor()
{
    stopTimer();
    for (auto* button : { &analyzeButton, &compareButton, &referenceButton, &historyButton,
                          &resetButton, &captureAButton, &captureBButton, &resetAButton,
                          &resetBButton, &swapButton, &refreshReferencesButton,
                          &chatToggleButton, &sendButton, &retryButton })
        button->onClick = nullptr;
    referenceSelector.onChange = nullptr;
    chatInput.onReturnKey = nullptr;
}

void AifredAudioProcessorEditor::DisplayMetric::setTarget(
    const aifred::analysis::MetricValue& value) noexcept
{
    if (! value.valid || ! std::isfinite(value.value))
    {
        clear();
        return;
    }
    target = static_cast<float>(value.value);
    if (! valid)
        current = target;
    valid = true;
}

void AifredAudioProcessorEditor::DisplayMetric::clear() noexcept
{
    current = target = 0.0f;
    valid = false;
}

bool AifredAudioProcessorEditor::DisplayMetric::advance(float amount) noexcept
{
    if (! valid)
        return false;
    const auto before = current;
    current += (target - current) * amount;
    if (std::abs(target - current) < 0.001f)
        current = target;
    return current != before;
}

void AifredAudioProcessorEditor::paint(juce::Graphics& g)
{
    juce::ColourGradient background(backgroundTop, 0.0f, 0.0f, backgroundBottom, 0.0f,
                                    static_cast<float>(getHeight()), false);
    g.setGradientFill(background);
    g.fillAll();

    auto bounds = getLocalBounds().toFloat().reduced(juce::jlimit(12.0f, 22.0f,
                                                                  getWidth() * 0.016f));
    drawHeader(g, bounds.removeFromTop(60.0f));
    drawModeNavigation(g, bounds.removeFromTop(42.0f));
    bounds.removeFromTop(12.0f);

    if (chatOpen)
    {
        auto chat = bounds.removeFromBottom(std::min(220.0f, bounds.getHeight() * 0.42f));
        bounds.removeFromBottom(10.0f);
        drawChatPanel(g, chat);
    }

    if (activeMode == Mode::analyze)
        drawAnalyzeMode(g, bounds);
    else if (activeMode == Mode::compare)
        drawCompareMode(g, bounds);
    else if (activeMode == Mode::reference)
        drawReferenceMode(g, bounds);
    else
        drawUnavailableMode(g, bounds, "HISTORY", "History is intentionally reserved for a later release.");
}

void AifredAudioProcessorEditor::resized()
{
    auto bounds = getLocalBounds().reduced(juce::jlimit(12, 22, getWidth() / 62));
    auto header = bounds.removeFromTop(60);
    resetButton.setBounds(header.removeFromRight(88).withSizeKeepingCentre(82, 30));
    chatToggleButton.setBounds(header.removeFromRight(116).withSizeKeepingCentre(108, 30));

    auto navigation = bounds.removeFromTop(42);
    navigation.removeFromLeft(2);
    for (auto* button : { &analyzeButton, &compareButton, &referenceButton, &historyButton })
    {
        button->setBounds(navigation.removeFromLeft(108));
        navigation.removeFromLeft(4);
    }

    profileSelector.setBounds(navigation.removeFromRight(230).reduced(2,4));
    bounds.removeFromTop(12);
    if (chatOpen)
    {
        auto chat = bounds.removeFromBottom(std::min(220, juce::roundToInt(bounds.getHeight() * 0.42f)));
        bounds.removeFromBottom(10);
        auto chatContent = chat.reduced(12);
        chatContent.removeFromTop(24);
        auto inputRow = chatContent.removeFromBottom(34);
        sendButton.setBounds(inputRow.removeFromRight(74));
        inputRow.removeFromRight(6);
        retryButton.setBounds(inputRow.removeFromRight(68));
        inputRow.removeFromRight(8);
        chatInput.setBounds(inputRow);
        chatContent.removeFromBottom(8);
        chatHistory.setBounds(chatContent);
    }
    chatHistory.setVisible(chatOpen);
    chatInput.setVisible(chatOpen);
    sendButton.setVisible(chatOpen);
    retryButton.setVisible(chatOpen);

    const auto supportHeight = juce::jlimit(144, 184, static_cast<int>(bounds.getHeight() * 0.29f));
    auto compareControls = bounds.removeFromTop(activeMode == Mode::compare ? 38 : 0);
    if (activeMode == Mode::compare)
    {
        for (auto* button : { &captureAButton, &captureBButton, &resetAButton, &resetBButton, &swapButton })
        {
            button->setBounds(compareControls.removeFromLeft(96).reduced(2, 3));
            compareControls.removeFromLeft(4);
        }
    }
    auto referenceControls = bounds.removeFromTop(activeMode == Mode::reference ? 42 : 0);
    if (activeMode == Mode::reference)
    {
        referenceSelector.setBounds(referenceControls.removeFromLeft(
            std::min(360, juce::roundToInt(referenceControls.getWidth() * 0.52f))).reduced(2, 4));
        referenceControls.removeFromLeft(6);
        refreshReferencesButton.setBounds(referenceControls.removeFromLeft(96).reduced(2, 4));
    }
    const auto referenceVisible = activeMode == Mode::reference;
    referenceSelector.setVisible(referenceVisible);
    refreshReferencesButton.setVisible(referenceVisible);
    bounds.removeFromBottom(supportHeight + 12);
    layoutWebVisualizer(bounds);
}

void AifredAudioProcessorEditor::timerCallback()
{
    const auto snapshot = processor.getViewSnapshot();
    if (! hasReceivedSnapshot || snapshot.sequence != lastSequence)
        acceptSnapshot(snapshot);

    bool changed = false;
    for (auto* metric : { &peak, &rms, &crest, &loudness, &width, &correlation })
        changed |= metric->advance(1.0f);
    changed |= spectrumBinWidthHz.advance(spectrumSmoothing);
    for (auto& bin : spectrumBins)
        changed |= bin.advance(spectrumSmoothing);

    publishVisualizationState();
    updateReferenceUi();
    updateChatUi();
    if (changed)
        repaint();
}

void AifredAudioProcessorEditor::acceptSnapshot(const aifred::analysis::ViewSnapshot& snapshot)
{
    latestSnapshot = snapshot;
    lastSequence = snapshot.sequence;
    hasReceivedSnapshot = true;
    peak.setTarget(snapshot.samplePeakDbfs);
    rms.setTarget(snapshot.rmsDbfs);
    crest.setTarget(snapshot.crestDb);
    loudness.setTarget(snapshot.shortTermLufs);
    width.setTarget(snapshot.width);
    correlation.setTarget(snapshot.correlation);
    spectrumBinWidthHz.setTarget(snapshot.spectrumBinWidthHz);
    for (std::size_t i = 0; i < spectrumBins.size(); ++i)
        spectrumBins[i].setTarget(snapshot.spectrumBins[i]);
    repaint();
}

void AifredAudioProcessorEditor::clearDisplay() noexcept
{
    latestSnapshot = {};
    for (auto* metric : { &peak, &rms, &crest, &loudness, &width, &correlation,
                          &spectrumBinWidthHz })
        metric->clear();
    for (auto& bin : spectrumBins)
        bin.clear();
}

void AifredAudioProcessorEditor::selectMode(Mode mode)
{
    activeMode = mode;
    if (activeMode == Mode::reference
        && aifred::services::ReferenceClient::instance().state().status
               == aifred::services::ReferenceCatalogStatus::idle)
        aifred::services::ReferenceClient::instance().refreshAsync();
    updateModeButtons();
    resized();
    repaint();
}

void AifredAudioProcessorEditor::updateModeButtons()
{
    analyzeButton.setToggleState(activeMode == Mode::analyze, juce::dontSendNotification);
    compareButton.setToggleState(activeMode == Mode::compare, juce::dontSendNotification);
    referenceButton.setToggleState(activeMode == Mode::reference, juce::dontSendNotification);
    historyButton.setToggleState(activeMode == Mode::history, juce::dontSendNotification);
    const auto compareVisible = activeMode == Mode::compare;
    for (auto* button : { &captureAButton, &captureBButton, &resetAButton, &resetBButton, &swapButton })
        button->setVisible(compareVisible);
}

void AifredAudioProcessorEditor::updateCompareButtons()
{
    resetAButton.setEnabled(captures.hasA());
    resetBButton.setEnabled(captures.hasB());
    swapButton.setEnabled(captures.hasA() || captures.hasB());
}

void AifredAudioProcessorEditor::updateReferenceUi()
{
    auto next = aifred::services::ReferenceClient::instance().state();
    if (next.revision == lastReferenceRevision)
        return;

    const auto previousId = selectedReference() != nullptr
        ? selectedReference()->id : std::string {};
    referenceCatalog = std::move(next);
    lastReferenceRevision = referenceCatalog.revision;
    referenceSelector.clear(juce::dontSendNotification);

    int selectedItem = 0;
    for (std::size_t index = 0; index < referenceCatalog.references.size(); ++index)
    {
        const auto itemId = static_cast<int>(index) + 1;
        const auto& reference = referenceCatalog.references[index];
        referenceSelector.addItem(juce::String(reference.name), itemId);
        if (reference.id == previousId)
            selectedItem = itemId;
    }
    if (selectedItem == 0 && ! referenceCatalog.references.empty())
        selectedItem = 1;
    referenceSelector.setSelectedId(selectedItem, juce::dontSendNotification);
    repaint();
}

void AifredAudioProcessorEditor::updateChatUi()
{
    if (++healthRefreshCounter >= refreshHz * 5)
    {
        healthRefreshCounter = 0;
        processor.intelligence().pingHealthAsync();
    }

    const auto health = processor.intelligence().health();
    if (health.revision != lastHealthRevision)
    {
        lastHealthRevision = health.revision;
        repaint();
    }

    const auto chat = processor.intelligence().lastChatResult();
    if (chat.revision != 0 && chat.revision != lastChatRevision)
    {
        lastChatRevision = chat.revision;
        processor.pipeline().recordResponse(juce::String(chat.success?chat.response:chat.error));
        appendConversationLine(chat.success ? "AIFRED" : "SYSTEM",
                               juce::String(chat.success ? chat.response : chat.error));
        repaint();
    }

    const auto sending = processor.intelligence().chatInFlight();
    sendButton.setEnabled(! sending);
    retryButton.setEnabled(! sending && lastQuestion.isNotEmpty());
    chatInput.setReadOnly(sending);
}

void AifredAudioProcessorEditor::sendChatQuestion()
{
    const auto question = chatInput.getText().trim();
    if (question.isEmpty())
        return;

    aifred::core::ReferenceDistribution reference;
    if(const auto* selected=selectedReference()) reference.id=selected->id;
    const auto mode=activeMode==Mode::compare ? "compare" : activeMode==Mode::reference ? "reference" : "analyze";
    const auto context = processor.pipeline().contextForQuestion(question,selectedReference()?&reference:nullptr,mode,captures.b()?&captures.b()->observation:nullptr);
    if (! processor.intelligence().askAsync(question, context))
        return;

    lastQuestion = question;
    appendConversationLine("YOU", question);
    chatInput.clear();
    updateChatUi();
    repaint();
}

void AifredAudioProcessorEditor::appendConversationLine(juce::StringRef speaker,
                                                         const juce::String& text)
{
    chatHistory.moveCaretToEnd();
    chatHistory.insertTextAtCaret(juce::String(speaker) + ": " + text.trim() + "\n\n");
    chatHistory.moveCaretToEnd();
}

const aifred::services::ReferenceProfile*
AifredAudioProcessorEditor::selectedReference() const noexcept
{
    const auto index = referenceSelector.getSelectedItemIndex();
    if (index < 0 || index >= static_cast<int>(referenceCatalog.references.size()))
        return nullptr;
    return &referenceCatalog.references[static_cast<std::size_t>(index)];
}

void AifredAudioProcessorEditor::drawHeader(juce::Graphics& g, juce::Rectangle<float> bounds) const
{
    auto brand = bounds.removeFromLeft(juce::jlimit(360.0f, 520.0f, bounds.getWidth() * 0.48f));
    g.setColour(textPrimary);
    g.setFont(makeFont(27.0f, juce::Font::bold));
    g.drawText("AIFRED 4.0", brand.removeFromLeft(188.0f), juce::Justification::centredLeft);
    g.setColour(textSecondary);
    g.setFont(makeFont(11.5f, juce::Font::bold));
    g.drawText("MIX INTELLIGENCE ENGINE", brand, juce::Justification::centredLeft);

    bounds.removeFromRight(96.0f);
    auto status = bounds.withSizeKeepingCentre(std::min(342.0f, bounds.getWidth()), 28.0f);
    const auto rate = processor.getCurrentSampleRate();
    const auto engineReady = rate > 0.0 && std::isfinite(rate);
    auto live = status.removeFromLeft(72.0f);
    g.setColour(engineReady ? aurora.withAlpha(0.13f) : panelStroke.withAlpha(0.42f));
    g.fillRoundedRectangle(live, 14.0f);
    g.setColour(engineReady ? aurora : textSecondary);
    g.fillEllipse(live.getX() + 10.0f, live.getCentreY() - 2.5f, 5.0f, 5.0f);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText(engineReady ? "LIVE" : "OFF", live.withTrimmedLeft(21.0f), juce::Justification::centredLeft);

    status.removeFromLeft(7.0f);
    auto sampleRate = status.removeFromLeft(104.0f);
    g.setColour(panelStroke.withAlpha(0.42f));
    g.fillRoundedRectangle(sampleRate, 14.0f);
    g.setColour(textSecondary);
    g.drawText(engineReady ? juce::String(rate / 1000.0, 1) + " kHz" : "-- kHz",
               sampleRate, juce::Justification::centred);
    status.removeFromLeft(7.0f);
    g.setColour(latestSnapshot.hasSignal ? aurora.withAlpha(0.12f) : panelStroke.withAlpha(0.42f));
    g.fillRoundedRectangle(status, 14.0f);
    g.setColour(latestSnapshot.hasSignal ? aurora : textSecondary);
    g.drawText(latestSnapshot.hasSignal ? "SIGNAL ACTIVE" : "NO SIGNAL", status,
               juce::Justification::centred);
}

void AifredAudioProcessorEditor::drawModeNavigation(juce::Graphics& g,
                                                     juce::Rectangle<float> bounds) const
{
    g.setColour(panelStroke.withAlpha(0.5f));
    g.drawHorizontalLine(static_cast<int>(bounds.getBottom() - 1.0f), bounds.getX(), bounds.getRight());
    const auto index = static_cast<int>(activeMode);
    g.setColour(cyan);
    g.fillRoundedRectangle(bounds.getX() + 2.0f + index * 112.0f, bounds.getBottom() - 2.0f,
                           108.0f, 2.0f, 1.0f);
    g.setColour(textSecondary.withAlpha(0.72f));
    g.setFont(makeFont(8.5f, juce::Font::bold));
    g.drawText(buildIdentityText(), bounds.removeFromRight(std::min(360.0f, bounds.getWidth() * 0.42f)),
               juce::Justification::centredRight);
}

void AifredAudioProcessorEditor::drawAnalyzeMode(juce::Graphics& g,
                                                  juce::Rectangle<float> bounds) const
{
    const auto supportHeight = juce::jlimit(144.0f, 184.0f, bounds.getHeight() * 0.29f);
    auto support = bounds.removeFromBottom(supportHeight);
    bounds.removeFromBottom(12.0f);
#if JUCE_WEB_BROWSER
    if (! webVisualizerReady)
#endif
        drawSpectrumHero(g, bounds);
    drawSupportMeters(g, support);
}

void AifredAudioProcessorEditor::drawCompareMode(juce::Graphics& g,
                                                  juce::Rectangle<float> bounds) const
{
    bounds.removeFromTop(38.0f);
    auto deltaPanel = bounds.removeFromBottom(96.0f);
    bounds.removeFromBottom(10.0f);
    auto aBounds = bounds.removeFromLeft((bounds.getWidth() - 10.0f) * 0.5f);
    bounds.removeFromLeft(10.0f);
    drawSnapshotSpectrum(g, aBounds, captures.a().get(), "MIX A");
    drawSnapshotSpectrum(g, bounds, captures.b().get(), "MIX B");

    drawPanel(g, deltaPanel);
    auto content = deltaPanel.reduced(14.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.0f, juce::Font::bold));
    g.drawText("B MINUS A", content.removeFromTop(16.0f), juce::Justification::centredLeft);
    const auto comparison = aifred::analysis::CaptureComparison::compare(captures);
    constexpr std::array<const char*, 6> labels { "PEAK", "RMS", "CREST", "LUFS", "WIDTH", "CORR" };
    const std::array<aifred::analysis::MetricValue, 6> values {
        comparison.samplePeakDbfs.delta, comparison.rmsDbfs.delta, comparison.crestDb.delta,
        comparison.shortTermLufs.delta, comparison.width.delta, comparison.correlation.delta
    };
    const auto cellWidth = content.getWidth() / static_cast<float>(labels.size());
    for (std::size_t i = 0; i < labels.size(); ++i)
    {
        auto cell = content.withX(content.getX() + cellWidth * static_cast<float>(i)).withWidth(cellWidth);
        g.setColour(textSecondary);
        g.setFont(makeFont(9.0f, juce::Font::bold));
        g.drawText(labels[i], cell.removeFromTop(16.0f), juce::Justification::centred);
        g.setColour(values[i].valid ? cyan : textSecondary);
        g.setFont(makeFont(14.0f, juce::Font::bold));
        const auto unit = i < 3 ? "dB" : i == 3 ? "LUFS" : "";
        g.drawText(metricText(values[i], i >= 4 ? 2 : 1, unit, true), cell,
                   juce::Justification::centred);
    }
}

void AifredAudioProcessorEditor::drawReferenceMode(juce::Graphics& g,
                                                    juce::Rectangle<float> bounds) const
{
    bounds.removeFromTop(42.0f);
    auto deltaPanel = bounds.removeFromBottom(96.0f);
    bounds.removeFromBottom(10.0f);
    auto currentBounds = bounds.removeFromLeft((bounds.getWidth() - 10.0f) * 0.5f);
    bounds.removeFromLeft(10.0f);
    drawSnapshotSpectrum(g, currentBounds, hasReceivedSnapshot ? &latestSnapshot : nullptr,
                         "CURRENT MIX");
    const auto* reference = selectedReference();
    drawReferenceMetrics(g, bounds, reference);

    drawPanel(g, deltaPanel);
    auto content = deltaPanel.reduced(14.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.0f, juce::Font::bold));
    g.drawText("REFERENCE MINUS CURRENT  /  MATCHED DEFINITIONS ONLY",
               content.removeFromTop(16.0f), juce::Justification::centredLeft);

    aifred::analysis::SnapshotComparison comparison;
    if (reference != nullptr && hasReceivedSnapshot)
    {
        const auto comparable = aifred::services::referenceAsComparableSnapshot(*reference);
        comparison = aifred::analysis::CaptureComparison::compare(latestSnapshot, comparable);
    }
    constexpr std::array<const char*, 6> labels { "PEAK", "RMS", "CREST", "SHORT LUFS", "WIDTH", "CORR" };
    const std::array<aifred::analysis::MetricValue, 6> values {
        comparison.samplePeakDbfs.delta, comparison.rmsDbfs.delta, comparison.crestDb.delta,
        comparison.shortTermLufs.delta, comparison.width.delta, comparison.correlation.delta
    };
    const auto cellWidth = content.getWidth() / static_cast<float>(labels.size());
    for (std::size_t i = 0; i < labels.size(); ++i)
    {
        auto cell = content.withX(content.getX() + cellWidth * static_cast<float>(i)).withWidth(cellWidth);
        g.setColour(textSecondary);
        g.setFont(makeFont(8.5f, juce::Font::bold));
        g.drawText(labels[i], cell.removeFromTop(16.0f), juce::Justification::centred);
        g.setColour(values[i].valid ? cyan : textSecondary);
        g.setFont(makeFont(13.0f, juce::Font::bold));
        const auto unit = i < 3 ? "dB" : i == 3 ? "LUFS" : "";
        g.drawText(metricText(values[i], i >= 4 ? 2 : 1, unit, true), cell,
                   juce::Justification::centred);
    }
}

void AifredAudioProcessorEditor::drawReferenceMetrics(
    juce::Graphics& g, juce::Rectangle<float> bounds,
    const aifred::services::ReferenceProfile* reference) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(14.0f);
    g.setColour(textPrimary);
    g.setFont(makeFont(12.0f, juce::Font::bold));
    g.drawText("SELECTED REFERENCE", content.removeFromTop(20.0f),
               juce::Justification::centredLeft);

    if (reference == nullptr)
    {
        g.setColour(textSecondary);
        g.setFont(makeFont(12.0f, juce::Font::bold));
        const auto message = referenceCatalog.message.empty()
            ? juce::String("REFRESH TO LOAD PRODUCTION REFERENCES")
            : juce::String(referenceCatalog.message);
        g.drawFittedText(message, content.toNearestInt(), juce::Justification::centred, 3);
        return;
    }

    g.setColour(aurora);
    g.setFont(makeFont(11.0f, juce::Font::bold));
    g.drawFittedText(juce::String(reference->name), content.removeFromTop(28.0f).toNearestInt(),
                     juce::Justification::centredLeft, 2);
    g.setColour(textSecondary);
    g.setFont(makeFont(8.0f));
    g.drawText(juce::String(reference->version), content.removeFromTop(14.0f),
               juce::Justification::centredLeft);

    auto legacySpectrum = content.removeFromTop(std::max(74.0f, content.getHeight() * 0.48f));
    legacySpectrum.reduce(0.0f, 8.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(8.5f, juce::Font::bold));
    g.drawText("STORED LEGACY SPECTRUM BANDS  /  NO HIGH-RES FFT FABRICATED",
               legacySpectrum.removeFromTop(15.0f), juce::Justification::centredLeft);

    bool hasSpectrum = false;
    const auto bandWidth = legacySpectrum.getWidth()
        / static_cast<float>(reference->metrics.legacySpectrumBandDbfs.size());
    for (std::size_t i = 0; i < reference->metrics.legacySpectrumBandDbfs.size(); ++i)
    {
        const auto& metric = reference->metrics.legacySpectrumBandDbfs[i];
        auto band = legacySpectrum.withX(legacySpectrum.getX() + bandWidth * static_cast<float>(i))
                                  .withWidth(std::max(1.0f, bandWidth - 3.0f));
        if (metric.valid && std::isfinite(metric.value))
        {
            hasSpectrum = true;
            const auto height = band.getHeight() * normalized(static_cast<float>(metric.value),
                                                               spectrumFloorDb, spectrumCeilingDb);
            g.setColour(aurora.withAlpha(0.72f));
            g.fillRoundedRectangle(band.withTop(band.getBottom() - height), 2.0f);
        }
    }
    if (! hasSpectrum)
    {
        g.setColour(textSecondary);
        g.setFont(makeFont(10.0f, juce::Font::bold));
        g.drawText("SPECTRUM UNAVAILABLE IN THIS RECORD", legacySpectrum,
                   juce::Justification::centred);
    }

    constexpr std::array<const char*, 8> labels {
        "PEAK", "TRUE PEAK", "RMS", "CREST", "SHORT LUFS", "INTEGRATED", "WIDTH", "CORR"
    };
    const std::array<aifred::analysis::MetricValue, 8> metrics {
        reference->metrics.samplePeakDbfs, reference->metrics.truePeakDbtp,
        reference->metrics.rmsDbfs, reference->metrics.crestDb,
        reference->metrics.shortTermLufs, reference->metrics.integratedLufs,
        reference->metrics.stereoWidth, reference->metrics.correlation
    };
    const auto rowHeight = std::max(25.0f, content.getHeight() * 0.5f);
    for (std::size_t i = 0; i < labels.size(); ++i)
    {
        const auto column = static_cast<int>(i % 4);
        const auto row = static_cast<int>(i / 4);
        auto cell = juce::Rectangle<float>(content.getX() + content.getWidth() * column / 4.0f,
                                           content.getY() + rowHeight * row,
                                           content.getWidth() / 4.0f, rowHeight);
        g.setColour(textSecondary);
        g.setFont(makeFont(7.5f, juce::Font::bold));
        g.drawText(labels[i], cell.removeFromTop(12.0f), juce::Justification::centred);
        g.setColour(metrics[i].valid ? textPrimary : textSecondary);
        g.setFont(makeFont(10.5f, juce::Font::bold));
        const auto unit = i == 1 ? "dBTP" : i == 4 || i == 5 ? "LUFS"
                         : i == 6 || i == 7 ? "" : "dB";
        g.drawText(metricText(metrics[i], i >= 6 ? 2 : 1, unit), cell,
                   juce::Justification::centredTop);
    }
}

void AifredAudioProcessorEditor::drawChatPanel(juce::Graphics& g,
                                                juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds, 10.0f);
    auto heading = bounds.reduced(12.0f).removeFromTop(20.0f);
    g.setColour(textPrimary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText("AIFRED CONVERSATION  /  SESSION ONLY", heading.removeFromLeft(260.0f),
               juce::Justification::centredLeft);

    const auto health = processor.intelligence().health();
    const auto sending = processor.intelligence().chatInFlight();
    juce::String status;
    juce::Colour statusColour = textSecondary;
    if (sending)
    {
        status = "WORKING";
        statusColour = cyan;
    }
    else if (! health.backendAvailable)
    {
        status = "BACKEND UNAVAILABLE";
        statusColour = danger;
    }
    else if (! health.providerAvailable)
    {
        status = "AI UNAVAILABLE";
        statusColour = danger;
    }
    else
    {
        status = juce::String(health.provider) + " / " + juce::String(health.model);
        statusColour = aurora;
    }
    g.setColour(statusColour);
    g.setFont(makeFont(9.0f, juce::Font::bold));
    g.drawText(status.toUpperCase(), heading, juce::Justification::centredRight);
}

void AifredAudioProcessorEditor::drawUnavailableMode(juce::Graphics& g,
                                                      juce::Rectangle<float> bounds,
                                                      juce::StringRef title,
                                                      juce::StringRef detail) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(36.0f);
    g.setColour(cyan.withAlpha(0.10f));
    g.fillEllipse(content.getCentreX() - 72.0f, content.getCentreY() - 72.0f, 144.0f, 144.0f);
    g.setColour(textPrimary);
    g.setFont(makeFont(24.0f, juce::Font::bold));
    g.drawText(title, content.removeFromTop(content.getHeight() * 0.48f), juce::Justification::centredBottom);
    content.removeFromTop(12.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(13.0f));
    g.drawFittedText(detail, content.toNearestInt(), juce::Justification::centredTop, 2);
}

void AifredAudioProcessorEditor::drawSpectrumHero(juce::Graphics& g,
                                                   juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds, 12.0f);
    auto content = bounds.reduced(18.0f);
    auto heading = content.removeFromTop(26.0f);
    g.setColour(textPrimary);
    g.setFont(makeFont(12.0f, juce::Font::bold));
    g.drawText("LIVE SPECTRUM", heading.removeFromLeft(160.0f), juce::Justification::centredLeft);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f));
    g.drawText("20 Hz - 20 kHz  /  PER-BIN dBFS  /  FIXED -96 TO 0 dB",
               heading, juce::Justification::centredRight);

    auto axisLabels = content.removeFromBottom(22.0f);
    auto dbLabels = content.removeFromLeft(38.0f);
    content.removeFromLeft(6.0f);
    const auto plot = content.withTrimmedBottom(2.0f);

    for (int db = -96; db <= 0; db += 12)
    {
        const auto y = juce::jmap(static_cast<float>(db), spectrumFloorDb, spectrumCeilingDb,
                                 plot.getBottom(), plot.getY());
        g.setColour(panelStroke.withAlpha(db % 24 == 0 ? 0.58f : 0.28f));
        g.drawHorizontalLine(juce::roundToInt(y), plot.getX(), plot.getRight());
        if (db % 24 == 0)
        {
            g.setColour(textSecondary.withAlpha(0.85f));
            g.setFont(makeFont(9.0f));
            g.drawText(juce::String(db), dbLabels.withY(y - 8.0f).withHeight(16.0f),
                       juce::Justification::centredRight);
        }
    }

    const auto binWidth = spectrumBinWidthHz.valid ? spectrumBinWidthHz.current : 0.0f;
    const auto availableMaximumHz = binWidth > 0.0f
        ? std::min(maximumFrequencyHz, binWidth * static_cast<float>(spectrumBins.size() - 1))
        : maximumFrequencyHz;
    for (const auto frequency : frequencyLandmarks)
    {
        if (frequency > availableMaximumHz + 0.5f)
            continue;
        const auto x = frequencyToX(frequency, plot);
        g.setColour(panelStroke.withAlpha(0.34f));
        g.drawVerticalLine(juce::roundToInt(x), plot.getY(), plot.getBottom());
        g.setColour(textSecondary);
        g.setFont(makeFont(9.0f));
        const auto labelBounds = axisLabels.withX(x - 17.0f).withWidth(34.0f);
        g.drawText(frequencyLabel(frequency), labelBounds,
                   frequency == 20.0f ? juce::Justification::centredLeft
                                      : frequency == 20000.0f ? juce::Justification::centredRight
                                                              : juce::Justification::centred);
    }

    juce::Path line;
    bool started = false;
    auto firstX = plot.getX();
    auto lastX = plot.getX();
    if (binWidth > 0.0f)
    {
        for (std::size_t index = 1; index < spectrumBins.size(); ++index)
        {
            const auto frequency = static_cast<float>(index) * binWidth;
            if (frequency < minimumFrequencyHz || frequency > availableMaximumHz)
                continue;
            const auto& bin = spectrumBins[index];
            if (! bin.valid)
                continue;
            const auto x = frequencyToX(frequency, plot);
            if (started && x - lastX < 0.6f)
                continue;
            const auto y = juce::jmap(juce::jlimit(spectrumFloorDb, spectrumCeilingDb, bin.current),
                                     spectrumFloorDb, spectrumCeilingDb,
                                     plot.getBottom(), plot.getY());
            if (! started)
            {
                line.startNewSubPath(x, y);
                firstX = x;
                started = true;
            }
            else
                line.lineTo(x, y);
            lastX = x;
        }
    }

    if (started)
    {
        auto fill = line;
        fill.lineTo(lastX, plot.getBottom());
        fill.lineTo(firstX, plot.getBottom());
        fill.closeSubPath();
        juce::ColourGradient energy(cyan.withAlpha(0.34f), plot.getX(), plot.getY(),
                                    aurora.withAlpha(0.02f), plot.getX(), plot.getBottom(), false);
        g.setGradientFill(energy);
        g.fillPath(fill);
        g.setColour(cyan.withAlpha(0.17f));
        g.strokePath(line, juce::PathStrokeType(5.0f, juce::PathStrokeType::curved,
                                               juce::PathStrokeType::rounded));
        g.setColour(cyan);
        g.strokePath(line, juce::PathStrokeType(1.7f, juce::PathStrokeType::curved,
                                               juce::PathStrokeType::rounded));
    }
    else
    {
        g.setColour(textSecondary);
        g.setFont(makeFont(13.0f, juce::Font::bold));
        g.drawText(latestSnapshot.hasSignal ? "BUILDING SPECTRUM" : "WAITING FOR LIVE AUDIO",
                   plot, juce::Justification::centred);
    }

    g.setColour(textSecondary.withAlpha(0.72f));
    g.setFont(makeFont(8.5f, juce::Font::bold));
    g.drawText(buildIdentityText(), bounds.reduced(18.0f).removeFromBottom(14.0f),
               juce::Justification::bottomRight);
}

void AifredAudioProcessorEditor::drawSnapshotSpectrum(
    juce::Graphics& g, juce::Rectangle<float> bounds,
    const aifred::analysis::ViewSnapshot* snapshot, juce::StringRef label) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(14.0f);
    g.setColour(textPrimary);
    g.setFont(makeFont(12.0f, juce::Font::bold));
    g.drawText(label, content.removeFromTop(20.0f), juce::Justification::centredLeft);

    if (snapshot == nullptr)
    {
        g.setColour(textSecondary);
        g.setFont(makeFont(12.0f, juce::Font::bold));
        g.drawText("NOT CAPTURED", content, juce::Justification::centred);
        return;
    }

    auto metrics = content.removeFromBottom(54.0f);
    auto spectrum = content.withTrimmedBottom(8.0f);
    const auto binWidth = snapshot->spectrumBinWidthHz.valid
        ? static_cast<float>(snapshot->spectrumBinWidthHz.value) : 0.0f;
    juce::Path path;
    bool started = false;
    if (binWidth > 0.0f)
    {
        for (std::size_t i = 1; i < snapshot->spectrumBins.size(); ++i)
        {
            const auto frequency = static_cast<float>(i) * binWidth;
            if (frequency < minimumFrequencyHz || frequency > maximumFrequencyHz)
                continue;
            const auto& bin = snapshot->spectrumBins[i];
            if (! bin.valid)
                continue;
            const auto x = frequencyToX(frequency, spectrum);
            const auto y = juce::jmap(juce::jlimit(spectrumFloorDb, spectrumCeilingDb,
                                                   static_cast<float>(bin.value)),
                                     spectrumFloorDb, spectrumCeilingDb,
                                     spectrum.getBottom(), spectrum.getY());
            if (! started) { path.startNewSubPath(x, y); started = true; }
            else path.lineTo(x, y);
        }
    }
    g.setColour(panelStroke.withAlpha(0.35f));
    for (const auto frequency : frequencyLandmarks)
        g.drawVerticalLine(juce::roundToInt(frequencyToX(frequency, spectrum)),
                           spectrum.getY(), spectrum.getBottom());
    if (started)
    {
        g.setColour(label == juce::StringRef("MIX A") ? cyan : aurora);
        g.strokePath(path, juce::PathStrokeType(1.4f));
    }

    constexpr std::array<const char*, 6> labels { "PEAK", "RMS", "CREST", "LUFS", "WIDTH", "CORR" };
    const std::array<aifred::analysis::MetricValue, 6> values {
        snapshot->samplePeakDbfs, snapshot->rmsDbfs, snapshot->crestDb,
        snapshot->shortTermLufs, snapshot->width, snapshot->correlation
    };
    const auto cellWidth = metrics.getWidth() / static_cast<float>(labels.size());
    for (std::size_t i = 0; i < labels.size(); ++i)
    {
        auto cell = metrics.withX(metrics.getX() + cellWidth * static_cast<float>(i)).withWidth(cellWidth);
        g.setColour(textSecondary);
        g.setFont(makeFont(8.0f, juce::Font::bold));
        g.drawText(labels[i], cell.removeFromTop(14.0f), juce::Justification::centred);
        g.setColour(textPrimary);
        g.setFont(makeFont(10.0f, juce::Font::bold));
        const auto unit = i < 3 ? "dB" : i == 3 ? "LUFS" : "";
        g.drawText(metricText(values[i], i >= 4 ? 2 : 1, unit), cell, juce::Justification::centred);
    }
}

void AifredAudioProcessorEditor::drawSupportMeters(juce::Graphics& g,
                                                    juce::Rectangle<float> bounds) const
{
    constexpr float gap = 10.0f;
    const auto cardWidth = (bounds.getWidth() - gap * 3.0f) * 0.25f;
    auto levelBounds = bounds.removeFromLeft(cardWidth);
    bounds.removeFromLeft(gap);
    auto dynamicsBounds = bounds.removeFromLeft(cardWidth);
    bounds.removeFromLeft(gap);
    auto loudnessBounds = bounds.removeFromLeft(cardWidth);
    bounds.removeFromLeft(gap);
    drawLevelCard(g, levelBounds);
    drawSingleMeterCard(g, dynamicsBounds, "DYNAMICS", "CREST", crest,
                        0.0f, 24.0f, "dB", 1, aurora);
    drawSingleMeterCard(g, loudnessBounds, "LOUDNESS", "SHORT-TERM", loudness,
                        -36.0f, 0.0f, "LUFS", 1, blue);
    drawStereoCard(g, bounds);
}

void AifredAudioProcessorEditor::drawLevelCard(juce::Graphics& g,
                                                juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(13.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    auto heading = content.removeFromTop(17.0f);
    g.drawText("LEVEL", heading, juce::Justification::centredLeft);
    if (latestSnapshot.sampleClipActive)
    {
        auto clip = heading.removeFromRight(48.0f);
        g.setColour(danger.withAlpha(0.16f));
        g.fillRoundedRectangle(clip, 4.0f);
        g.setColour(danger);
        g.drawText("CLIP", clip, juce::Justification::centred);
    }
    auto values = content.removeFromBottom(42.0f);
    auto arcArea = content.reduced(3.0f, 0.0f);
    const auto diameter = std::min(arcArea.getWidth(), arcArea.getHeight() * 1.35f);
    auto arcBounds = juce::Rectangle<float>(diameter, diameter)
                         .withCentre({ arcArea.getCentreX(), arcArea.getCentreY() + diameter * 0.13f });
    drawArc(g, arcBounds, peak.valid ? normalized(peak.current, -60.0f, 0.0f) : 0.0f, cyan, 7.0f);
    drawArc(g, arcBounds.reduced(12.0f),
            rms.valid ? normalized(rms.current, -60.0f, 0.0f) : 0.0f, aurora, 5.0f);
    auto left = values.removeFromLeft(values.getWidth() * 0.5f).reduced(1.0f);
    auto right = values.reduced(1.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.0f, juce::Font::bold));
    g.drawText("PEAK", left.removeFromTop(13.0f), juce::Justification::centred);
    g.drawText("RMS", right.removeFromTop(13.0f), juce::Justification::centred);
    drawMetricValue(g, left, peak, "dBFS", 1, cyan);
    drawMetricValue(g, right, rms, "dBFS", 1, aurora);
}

void AifredAudioProcessorEditor::drawSingleMeterCard(
    juce::Graphics& g, juce::Rectangle<float> bounds, juce::StringRef title,
    juce::StringRef caption, const DisplayMetric& metric, float minimum, float maximum,
    juce::StringRef unit, int decimals, juce::Colour accent) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(13.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText(title, content.removeFromTop(17.0f), juce::Justification::centredLeft);
    auto values = content.removeFromBottom(42.0f);
    auto arcArea = content.reduced(3.0f, 0.0f);
    const auto diameter = std::min(arcArea.getWidth(), arcArea.getHeight() * 1.35f);
    auto arcBounds = juce::Rectangle<float>(diameter, diameter)
                         .withCentre({ arcArea.getCentreX(), arcArea.getCentreY() + diameter * 0.13f });
    drawArc(g, arcBounds, metric.valid ? normalized(metric.current, minimum, maximum) : 0.0f,
            accent, 7.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.0f, juce::Font::bold));
    g.drawText(caption, values.removeFromTop(13.0f), juce::Justification::centred);
    drawMetricValue(g, values, metric, unit, decimals, accent);
}

void AifredAudioProcessorEditor::drawStereoCard(juce::Graphics& g,
                                                 juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(13.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText("STEREO", content.removeFromTop(17.0f), juce::Justification::centredLeft);
    auto values = content.removeFromBottom(42.0f);
    auto arcArea = content.reduced(3.0f, 0.0f);
    const auto diameter = std::min(arcArea.getWidth(), arcArea.getHeight() * 1.35f);
    auto arcBounds = juce::Rectangle<float>(diameter, diameter)
                         .withCentre({ arcArea.getCentreX(), arcArea.getCentreY() + diameter * 0.13f });
    drawArc(g, arcBounds, width.valid ? normalized(width.current, 0.0f, 1.0f) : 0.0f, cyan, 7.0f);
    drawArc(g, arcBounds.reduced(12.0f),
            correlation.valid ? normalized(correlation.current, -1.0f, 1.0f) : 0.0f,
            correlation.valid && correlation.current < 0.0f ? danger : aurora, 5.0f);
    auto left = values.removeFromLeft(values.getWidth() * 0.5f).reduced(1.0f);
    auto right = values.reduced(1.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.0f, juce::Font::bold));
    g.drawText("WIDTH", left.removeFromTop(13.0f), juce::Justification::centred);
    g.drawText("CORRELATION", right.removeFromTop(13.0f), juce::Justification::centred);
    g.setColour(width.valid ? cyan : textSecondary);
    g.setFont(makeFont(14.0f, juce::Font::bold));
    g.drawText(width.valid ? juce::String(juce::roundToInt(width.current * 100.0f)) + "%" : "--",
               left, juce::Justification::centred);
    g.setColour(correlation.valid && correlation.current < 0.0f ? danger
                                                                 : correlation.valid ? aurora : textSecondary);
    g.drawText(formattedValue(correlation, "", 2, true), right, juce::Justification::centred);
}

void AifredAudioProcessorEditor::drawPanel(juce::Graphics& g, juce::Rectangle<float> bounds,
                                            float corner) const
{
    juce::ColourGradient panel(panelTop, bounds.getX(), bounds.getY(), panelBottom,
                               bounds.getRight(), bounds.getBottom(), false);
    g.setGradientFill(panel);
    g.fillRoundedRectangle(bounds, corner);
    g.setColour(panelStroke.withAlpha(0.74f));
    g.drawRoundedRectangle(bounds.reduced(0.5f), corner, 1.0f);
}

void AifredAudioProcessorEditor::drawArc(juce::Graphics& g, juce::Rectangle<float> bounds,
                                         float amount, juce::Colour accent, float thickness) const
{
    constexpr float start = juce::MathConstants<float>::pi * 1.25f;
    constexpr float end = juce::MathConstants<float>::pi * 2.75f;
    const auto radius = std::max(1.0f, std::min(bounds.getWidth(), bounds.getHeight()) * 0.5f
                                      - thickness * 0.5f);
    juce::Path track;
    track.addCentredArc(bounds.getCentreX(), bounds.getCentreY(), radius, radius,
                        0.0f, start, end, true);
    g.setColour(panelStroke.withAlpha(0.62f));
    g.strokePath(track, juce::PathStrokeType(thickness, juce::PathStrokeType::curved,
                                            juce::PathStrokeType::rounded));
    if (amount <= 0.0f)
        return;
    juce::Path value;
    value.addCentredArc(bounds.getCentreX(), bounds.getCentreY(), radius, radius, 0.0f,
                        start + 0.01f, start + (end - start) * juce::jlimit(0.0f, 1.0f, amount), true);
    g.setColour(accent.withAlpha(0.16f));
    g.strokePath(value, juce::PathStrokeType(thickness + 4.0f, juce::PathStrokeType::curved,
                                            juce::PathStrokeType::rounded));
    g.setColour(accent);
    g.strokePath(value, juce::PathStrokeType(thickness, juce::PathStrokeType::curved,
                                            juce::PathStrokeType::rounded));
}

void AifredAudioProcessorEditor::drawMetricValue(juce::Graphics& g,
                                                  juce::Rectangle<float> bounds,
                                                  const DisplayMetric& metric,
                                                  juce::StringRef unit, int decimals,
                                                  juce::Colour colour) const
{
    g.setColour(metric.valid ? colour : textSecondary);
    g.setFont(makeFont(14.0f, juce::Font::bold));
    g.drawText(formattedValue(metric, unit, decimals), bounds, juce::Justification::centred);
}

AifredAudioProcessorEditor::VisualizationState
AifredAudioProcessorEditor::makeVisualizationState() const noexcept
{
    VisualizationState state;
    state.normalizedPeak = peak.valid ? normalized(peak.current, -60.0f, 0.0f) : 0.0f;
    state.normalizedRms = rms.valid ? normalized(rms.current, -60.0f, 0.0f) : 0.0f;
    state.normalizedCrest = crest.valid ? normalized(crest.current, 0.0f, 24.0f) : 0.0f;
    state.normalizedLoudness = loudness.valid ? normalized(loudness.current, -36.0f, 0.0f) : 0.0f;
    state.width = width.valid ? juce::jlimit(0.0f, 1.0f, width.current) : 0.0f;
    state.correlation = correlation.valid ? juce::jlimit(-1.0f, 1.0f, correlation.current) : 0.0f;
    state.signalActive = latestSnapshot.hasSignal;
    state.elapsedSeconds = latestSnapshot.elapsedSeconds;
    state.spectrumBinWidthHz = spectrumBinWidthHz.valid ? spectrumBinWidthHz.current : 0.0;
    for (std::size_t i = 0; i < spectrumBins.size(); ++i)
    {
        state.spectrumBins[i] = spectrumBins[i].current;
        state.spectrumValid[i] = spectrumBins[i].valid;
    }
    return state;
}

void AifredAudioProcessorEditor::publishVisualizationState()
{
#if JUCE_WEB_BROWSER
    if (webVisualizer == nullptr || ! webVisualizerReady || activeMode != Mode::analyze)
        return;

    const auto state = makeVisualizationState();
    auto object = std::make_unique<juce::DynamicObject>();
    object->setProperty("normalizedPeak", state.normalizedPeak);
    object->setProperty("normalizedRms", state.normalizedRms);
    object->setProperty("normalizedCrest", state.normalizedCrest);
    object->setProperty("normalizedLoudness", state.normalizedLoudness);
    object->setProperty("width", state.width);
    object->setProperty("correlation", state.correlation);
    object->setProperty("signalActive", state.signalActive);
    object->setProperty("elapsedSeconds", state.elapsedSeconds);
    object->setProperty("spectrumBinWidthHz", state.spectrumBinWidthHz);
    juce::Array<juce::var> bins;
    bins.ensureStorageAllocated(static_cast<int>(state.spectrumBins.size()));
    for (std::size_t i = 0; i < state.spectrumBins.size(); ++i)
        bins.add(state.spectrumValid[i] ? juce::var(state.spectrumBins[i]) : juce::var());
    object->setProperty("spectrumBins", bins);
    webVisualizer->emitEventIfBrowserIsVisible("aifredVisualizationState", juce::var(object.release()));
#endif
}

void AifredAudioProcessorEditor::initialiseWebVisualizer()
{
#if JUCE_WEB_BROWSER && JUCE_WEB_BROWSER_RESOURCE_PROVIDER_AVAILABLE
    auto options = juce::WebBrowserComponent::Options {}
        .withBackend(juce::WebBrowserComponent::Options::Backend::webview2)
        .withKeepPageLoadedWhenBrowserIsHidden()
        .withWinWebView2Options(juce::WebBrowserComponent::Options::WinWebView2 {}
            .withStatusBarDisabled()
            .withBuiltInErrorPageDisabled()
            .withBackgroundColour(juce::Colours::transparentBlack))
        .withNativeIntegrationEnabled()
        .withEventListener("aifredVisualizerReady", [this] (const juce::var&)
        {
            webVisualizerReady = true;
            resized();
            repaint();
        })
        .withEventListener("aifredVisualizerFailed", [this] (const juce::var&)
        {
            webVisualizerReady = false;
            resized();
            repaint();
        })
        .withResourceProvider([] (const juce::String& path)
            -> std::optional<juce::WebBrowserComponent::Resource>
        {
            if (path == "/" || path == "/index.html")
                return makeWebResource(AifredVisualizationAssets::index_html,
                                       AifredVisualizationAssets::index_htmlSize, "text/html");
            if (path == "/visualizer.css")
                return makeWebResource(AifredVisualizationAssets::visualizer_css,
                                       AifredVisualizationAssets::visualizer_cssSize, "text/css");
            if (path == "/visualizer.js")
                return makeWebResource(AifredVisualizationAssets::visualizer_js,
                                       AifredVisualizationAssets::visualizer_jsSize, "text/javascript");
            if (path == "/three.module.min.js")
                return makeWebResource(AifredVisualizationAssets::three_module_min_js,
                                       AifredVisualizationAssets::three_module_min_jsSize,
                                       "text/javascript");
            return std::nullopt;
        });

    if (juce::WebBrowserComponent::areOptionsSupported(options))
    {
        webVisualizer = std::make_unique<juce::WebBrowserComponent>(options);
        addChildComponent(*webVisualizer);
        webVisualizer->goToURL(juce::WebBrowserComponent::getResourceProviderRoot());
    }
#endif
}

void AifredAudioProcessorEditor::layoutWebVisualizer(juce::Rectangle<int> heroBounds)
{
#if JUCE_WEB_BROWSER
    if (webVisualizer != nullptr)
    {
        webVisualizer->setBounds(heroBounds);
        webVisualizer->setVisible(webVisualizerReady && activeMode == Mode::analyze);
    }
#else
    juce::ignoreUnused(heroBounds);
#endif
}

float AifredAudioProcessorEditor::normalized(float value, float minimum, float maximum) noexcept
{
    if (! std::isfinite(value) || maximum <= minimum)
        return 0.0f;
    return juce::jlimit(0.0f, 1.0f, (value - minimum) / (maximum - minimum));
}

juce::String AifredAudioProcessorEditor::formattedValue(const DisplayMetric& metric,
                                                         juce::StringRef unit,
                                                         int decimals,
                                                         bool showPlus)
{
    if (! metric.valid)
        return "--";
    auto value = juce::String(metric.current, decimals);
    if (showPlus && metric.current > 0.0f)
        value = "+" + value;
    return unit.isEmpty() ? value : value + " " + unit;
}
