#include "PluginEditor.h"

#include <algorithm>
#include <cmath>

namespace
{
constexpr int kRefreshHz = 45;
constexpr float kSmoothing = 0.30f;

const juce::Colour backgroundTop { 0xff080c13 };
const juce::Colour backgroundBottom { 0xff030507 };
const juce::Colour panelTop { 0xff121a24 };
const juce::Colour panelBottom { 0xff0a1018 };
const juce::Colour panelStroke { 0xff253241 };
const juce::Colour textPrimary { 0xffeef7fb };
const juce::Colour textSecondary { 0xff8fa4b3 };
const juce::Colour cyan { 0xff4bdcf2 };
const juce::Colour aurora { 0xff60efb3 };
const juce::Colour blue { 0xff6fa8ff };
const juce::Colour amber { 0xffffbd63 };
const juce::Colour danger { 0xffff6e72 };

constexpr std::array<const char*, 7> bandLabels {
    "60", "120", "250", "500", "1k", "4k", "10k"
};

juce::Font makeFont(float height, juce::Font::FontStyleFlags style = juce::Font::plain)
{
    return juce::Font(juce::FontOptions(height, style));
}

juce::Rectangle<float> reducedTop(juce::Rectangle<float>& bounds, float amount)
{
    return bounds.removeFromTop(std::min(amount, bounds.getHeight()));
}
}

AifredAudioProcessorEditor::AifredAudioProcessorEditor(AifredAudioProcessor& owner)
    : AudioProcessorEditor(&owner), processor(owner)
{
    setOpaque(true);
    setResizable(true, true);
    setResizeLimits(920, 600, 1600, 1100);
    setSize(1120, 720);

    resetButton.setColour(juce::TextButton::buttonColourId, juce::Colour(0xff142532));
    resetButton.setColour(juce::TextButton::buttonOnColourId, juce::Colour(0xff142532));
    resetButton.setColour(juce::TextButton::textColourOffId, textPrimary);
    resetButton.setColour(juce::TextButton::textColourOnId, textPrimary);
    resetButton.setMouseCursor(juce::MouseCursor::PointingHandCursor);
    resetButton.onClick = [this]
    {
        processor.resetAnalysis();
        clearDisplay();
        hasReceivedSnapshot = false;
        lastSequence = 0;
        repaint();
    };
    addAndMakeVisible(resetButton);

    acceptSnapshot(processor.getAnalysisSnapshot());
    startTimerHz(kRefreshHz);
}

AifredAudioProcessorEditor::~AifredAudioProcessorEditor()
{
    stopTimer();
    resetButton.onClick = nullptr;
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
    current = 0.0f;
    target = 0.0f;
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
    juce::ColourGradient background(backgroundTop, 0.0f, 0.0f,
                                    backgroundBottom, 0.0f, static_cast<float>(getHeight()), false);
    g.setGradientFill(background);
    g.fillAll();

    auto bounds = getLocalBounds().toFloat().reduced(18.0f);
    auto header = reducedTop(bounds, 82.0f);
    drawHeader(g, header);
    bounds.removeFromTop(12.0f);

    const auto findingWidth = juce::jlimit(220.0f, 290.0f, bounds.getWidth() * 0.245f);
    auto finding = bounds.removeFromRight(findingWidth);
    bounds.removeFromRight(12.0f);

    const auto spectrumHeight = juce::jlimit(150.0f, 220.0f, bounds.getHeight() * 0.34f);
    auto spectrumBounds = bounds.removeFromBottom(spectrumHeight);
    bounds.removeFromBottom(12.0f);

    drawMeterWorkspace(g, bounds);
    drawSpectrum(g, spectrumBounds);
    drawFindingPanel(g, finding);
}

void AifredAudioProcessorEditor::resized()
{
    auto header = getLocalBounds().reduced(18).removeFromTop(82);
    resetButton.setBounds(header.removeFromRight(92).withSizeKeepingCentre(86, 34));
}

void AifredAudioProcessorEditor::timerCallback()
{
    const auto snapshot = processor.getAnalysisSnapshot();
    if (! hasReceivedSnapshot || snapshot.sequence != lastSequence)
        acceptSnapshot(snapshot);

    bool changed = false;
    changed |= peak.advance(kSmoothing);
    changed |= rms.advance(kSmoothing);
    changed |= crest.advance(kSmoothing);
    changed |= loudness.advance(kSmoothing);
    changed |= width.advance(kSmoothing);
    changed |= correlation.advance(kSmoothing);
    for (auto& band : spectrum)
        changed |= band.advance(kSmoothing);

    if (changed)
        repaint();
}

void AifredAudioProcessorEditor::acceptSnapshot(
    const aifred::analysis::AnalysisSnapshot& snapshot)
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
    for (std::size_t i = 0; i < spectrum.size(); ++i)
        spectrum[i].setTarget(snapshot.spectrumBands[i]);

    repaint();
}

void AifredAudioProcessorEditor::clearDisplay() noexcept
{
    latestSnapshot = {};
    peak.clear();
    rms.clear();
    crest.clear();
    loudness.clear();
    width.clear();
    correlation.clear();
    for (auto& band : spectrum)
        band.clear();
}

void AifredAudioProcessorEditor::drawHeader(juce::Graphics& g,
                                             juce::Rectangle<float> bounds) const
{
    g.setColour(textPrimary);
    g.setFont(makeFont(27.0f, juce::Font::bold));
    g.drawText("AIFRED 4.0", bounds.removeFromLeft(190.0f), juce::Justification::centredLeft);

    auto identity = bounds.removeFromLeft(245.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(13.0f));
    g.drawText("MIX INTELLIGENCE ENGINE", identity, juce::Justification::centredLeft);

    bounds.removeFromRight(102.0f);
    const auto statusY = bounds.getCentreY() - 15.0f;
    auto status = bounds.withY(statusY).withHeight(30.0f);
    const auto rate = processor.getCurrentSampleRate();
    const auto engineReady = rate > 0.0 && std::isfinite(rate);

    auto live = status.removeFromLeft(78.0f);
    g.setColour(engineReady ? aurora.withAlpha(0.16f) : panelStroke.withAlpha(0.45f));
    g.fillRoundedRectangle(live, 15.0f);
    g.setColour(engineReady ? aurora : textSecondary);
    g.fillEllipse(live.getX() + 11.0f, live.getCentreY() - 3.0f, 6.0f, 6.0f);
    g.setFont(makeFont(11.0f, juce::Font::bold));
    g.drawText(engineReady ? "LIVE" : "OFF", live.withTrimmedLeft(23.0f),
               juce::Justification::centredLeft);

    status.removeFromLeft(8.0f);
    auto sampleRate = status.removeFromLeft(118.0f);
    g.setColour(panelStroke.withAlpha(0.45f));
    g.fillRoundedRectangle(sampleRate, 15.0f);
    g.setColour(textSecondary);
    const auto rateText = engineReady
        ? juce::String(rate / 1000.0, 1) + " kHz"
        : juce::String("-- kHz");
    g.drawText(rateText, sampleRate, juce::Justification::centred);

    status.removeFromLeft(8.0f);
    auto signal = status.removeFromLeft(126.0f);
    g.setColour(panelStroke.withAlpha(0.45f));
    g.fillRoundedRectangle(signal, 15.0f);
    g.setColour(latestSnapshot.hasSignal ? aurora : textSecondary);
    g.drawText(latestSnapshot.hasSignal ? "SIGNAL ACTIVE" : "NO SIGNAL", signal,
               juce::Justification::centred);
}

void AifredAudioProcessorEditor::drawMeterWorkspace(juce::Graphics& g,
                                                     juce::Rectangle<float> bounds) const
{
    constexpr float gap = 12.0f;
    auto top = bounds.removeFromTop((bounds.getHeight() - gap) * 0.5f);
    bounds.removeFromTop(gap);

    auto topLeft = top.removeFromLeft((top.getWidth() - gap) * 0.5f);
    top.removeFromLeft(gap);
    auto bottomLeft = bounds.removeFromLeft((bounds.getWidth() - gap) * 0.5f);
    bounds.removeFromLeft(gap);

    drawLevelCard(g, topLeft);
    drawSingleMeterCard(g, top, "DYNAMICS ARC", "CREST", crest, 0.0f, 24.0f,
                        "dB", 1, aurora);
    drawSingleMeterCard(g, bottomLeft, "LOUDNESS ARC", "SHORT-TERM", loudness,
                        -36.0f, 0.0f, "LUFS", 1, blue);
    drawStereoCard(g, bounds);
}

void AifredAudioProcessorEditor::drawLevelCard(juce::Graphics& g,
                                                juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(14.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText("LEVEL ARC", content.removeFromTop(18.0f), juce::Justification::centredLeft);

    auto values = content.removeFromBottom(44.0f);
    auto arcArea = content.reduced(4.0f, 2.0f);
    const auto diameter = std::min(arcArea.getWidth(), arcArea.getHeight() * 1.34f);
    auto arcBounds = juce::Rectangle<float>(diameter, diameter)
                         .withCentre({ arcArea.getCentreX(), arcArea.getCentreY() + diameter * 0.13f });
    drawArc(g, arcBounds, peak.valid ? normalized(peak.current, -60.0f, 0.0f) : 0.0f,
            cyan, 8.0f);
    drawArc(g, arcBounds.reduced(13.0f),
            rms.valid ? normalized(rms.current, -60.0f, 0.0f) : 0.0f, aurora, 6.0f);

    auto left = values.removeFromLeft(values.getWidth() * 0.5f).reduced(2.0f);
    auto right = values.reduced(2.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.5f, juce::Font::bold));
    g.drawText("PEAK", left.removeFromTop(14.0f), juce::Justification::centred);
    g.drawText("RMS", right.removeFromTop(14.0f), juce::Justification::centred);
    drawMetricValue(g, left, peak, "dBFS", 1, cyan);
    drawMetricValue(g, right, rms, "dBFS", 1, aurora);
}

void AifredAudioProcessorEditor::drawSingleMeterCard(
    juce::Graphics& g, juce::Rectangle<float> bounds, juce::StringRef title,
    juce::StringRef caption, const DisplayMetric& metric, float minimum, float maximum,
    juce::StringRef unit, int decimals, juce::Colour accent) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(14.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText(title, content.removeFromTop(18.0f), juce::Justification::centredLeft);

    auto values = content.removeFromBottom(44.0f);
    auto arcArea = content.reduced(4.0f, 0.0f);
    const auto diameter = std::min(arcArea.getWidth(), arcArea.getHeight() * 1.34f);
    auto arcBounds = juce::Rectangle<float>(diameter, diameter)
                         .withCentre({ arcArea.getCentreX(), arcArea.getCentreY() + diameter * 0.12f });
    drawArc(g, arcBounds,
            metric.valid ? normalized(metric.current, minimum, maximum) : 0.0f,
            accent, 8.0f);

    g.setColour(textSecondary);
    g.setFont(makeFont(9.5f, juce::Font::bold));
    g.drawText(caption, values.removeFromTop(14.0f), juce::Justification::centred);
    drawMetricValue(g, values, metric, unit, decimals, accent);
}

void AifredAudioProcessorEditor::drawStereoCard(juce::Graphics& g,
                                                 juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(14.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText("STEREO ARC", content.removeFromTop(18.0f), juce::Justification::centredLeft);

    auto values = content.removeFromBottom(44.0f);
    auto arcArea = content.reduced(4.0f, 0.0f);
    const auto diameter = std::min(arcArea.getWidth(), arcArea.getHeight() * 1.34f);
    auto arcBounds = juce::Rectangle<float>(diameter, diameter)
                         .withCentre({ arcArea.getCentreX(), arcArea.getCentreY() + diameter * 0.12f });
    drawArc(g, arcBounds, width.valid ? normalized(width.current, 0.0f, 1.0f) : 0.0f,
            cyan, 8.0f);
    drawArc(g, arcBounds.reduced(13.0f),
            correlation.valid ? normalized(correlation.current, -1.0f, 1.0f) : 0.0f,
            correlation.valid && correlation.current < 0.0f ? danger : aurora, 6.0f);

    auto left = values.removeFromLeft(values.getWidth() * 0.5f).reduced(2.0f);
    auto right = values.reduced(2.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.5f, juce::Font::bold));
    g.drawText("WIDTH", left.removeFromTop(14.0f), juce::Justification::centred);
    g.drawText("CORRELATION", right.removeFromTop(14.0f), juce::Justification::centred);

    g.setColour(cyan);
    g.setFont(makeFont(15.0f, juce::Font::bold));
    g.drawText(width.valid ? juce::String(juce::roundToInt(width.current * 100.0f)) + "%" : "--",
               left, juce::Justification::centred);
    g.setColour(correlation.valid && correlation.current < 0.0f ? danger : aurora);
    g.drawText(formattedValue(correlation, "", 2, true), right, juce::Justification::centred);
}

void AifredAudioProcessorEditor::drawSpectrum(juce::Graphics& g,
                                               juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(16.0f);
    auto title = content.removeFromTop(22.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText("SPECTRUM  /  BAND LEVEL dBFS  /  CENTER Hz", title,
               juce::Justification::centredLeft);

    auto labels = content.removeFromBottom(21.0f);
    content.removeFromBottom(3.0f);
    const auto gap = juce::jlimit(4.0f, 10.0f, content.getWidth() * 0.012f);
    const auto bandWidth = (content.getWidth() - gap * 6.0f) / 7.0f;

    for (std::size_t i = 0; i < spectrum.size(); ++i)
    {
        const auto x = content.getX() + static_cast<float>(i) * (bandWidth + gap);
        auto slot = juce::Rectangle<float>(x, content.getY(), bandWidth, content.getHeight());
        g.setColour(panelStroke.withAlpha(0.38f));
        g.fillRoundedRectangle(slot, 4.0f);

        if (spectrum[i].valid)
        {
            const auto amount = normalized(spectrum[i].current, -72.0f, 0.0f);
            auto fill = slot.withTop(slot.getBottom() - slot.getHeight() * amount);
            juce::ColourGradient energy(cyan.withAlpha(0.92f), fill.getX(), fill.getY(),
                                        aurora.withAlpha(0.56f), fill.getX(), fill.getBottom(), false);
            g.setGradientFill(energy);
            g.fillRoundedRectangle(fill, 4.0f);
        }

        auto label = juce::Rectangle<float>(x, labels.getY(), bandWidth, labels.getHeight());
        g.setColour(textSecondary);
        g.setFont(makeFont(10.0f));
        g.drawText(bandLabels[i], label, juce::Justification::centred);
    }

}

void AifredAudioProcessorEditor::drawFindingPanel(juce::Graphics& g,
                                                   juce::Rectangle<float> bounds) const
{
    drawPanel(g, bounds);
    auto content = bounds.reduced(18.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(10.0f, juce::Font::bold));
    g.drawText("AIFRED FINDING", content.removeFromTop(20.0f), juce::Justification::centredLeft);

    content.removeFromTop(18.0f);
    const auto finding = currentFinding();
    const auto isWarning = finding == "VERY HIGH PEAK" || finding == "NEGATIVE CORRELATION";
    const auto findingColour = isWarning ? (finding == "NEGATIVE CORRELATION" ? danger : amber)
                                         : (latestSnapshot.hasSignal ? aurora : textSecondary);
    g.setColour(findingColour.withAlpha(0.14f));
    auto badge = content.removeFromTop(44.0f);
    g.fillRoundedRectangle(badge, 8.0f);
    g.setColour(findingColour);
    g.setFont(makeFont(12.0f, juce::Font::bold));
    g.drawFittedText(finding, badge.toNearestInt().reduced(10, 4),
                     juce::Justification::centredLeft, 1);

    content.removeFromTop(18.0f);
    g.setColour(textPrimary);
    g.setFont(makeFont(18.0f, juce::Font::bold));
    g.drawText(latestSnapshot.hasSignal ? "Listening now" : "Waiting for audio",
               content.removeFromTop(30.0f), juce::Justification::centredLeft);

    content.removeFromTop(8.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(12.0f));
    const juce::String description = latestSnapshot.hasSignal
        ? "This alpha reports deterministic observations from the live analysis snapshot."
        : "Route audio through AIFRED, then press play. Last useful readings remain visible when playback stops.";
    g.drawFittedText(description, content.removeFromTop(88.0f).toNearestInt(),
                     juce::Justification::topLeft, 5);

    auto footer = bounds.reduced(18.0f).removeFromBottom(62.0f);
    g.setColour(panelStroke.withAlpha(0.7f));
    g.drawHorizontalLine(static_cast<int>(footer.getY()), footer.getX(), footer.getRight());
    footer.removeFromTop(12.0f);
    g.setColour(textSecondary);
    g.setFont(makeFont(9.0f, juce::Font::bold));
    g.drawText("4.0.0-alpha.1  /  NATIVE DSP", footer, juce::Justification::bottomLeft);
}

void AifredAudioProcessorEditor::drawPanel(juce::Graphics& g,
                                            juce::Rectangle<float> bounds) const
{
    juce::ColourGradient panel(panelTop, bounds.getX(), bounds.getY(),
                               panelBottom, bounds.getRight(), bounds.getBottom(), false);
    g.setGradientFill(panel);
    g.fillRoundedRectangle(bounds, 10.0f);
    g.setColour(panelStroke.withAlpha(0.75f));
    g.drawRoundedRectangle(bounds.reduced(0.5f), 10.0f, 1.0f);
}

void AifredAudioProcessorEditor::drawArc(juce::Graphics& g,
                                         juce::Rectangle<float> bounds,
                                         float amount, juce::Colour accent,
                                         float thickness) const
{
    constexpr float start = juce::MathConstants<float>::pi * 1.25f;
    constexpr float end = juce::MathConstants<float>::pi * 2.75f;
    const auto radius = std::max(1.0f, std::min(bounds.getWidth(), bounds.getHeight()) * 0.5f
                                      - thickness * 0.5f);

    juce::Path track;
    track.addCentredArc(bounds.getCentreX(), bounds.getCentreY(), radius, radius,
                        0.0f, start, end, true);
    g.setColour(panelStroke.withAlpha(0.62f));
    g.strokePath(track, juce::PathStrokeType(thickness,
                 juce::PathStrokeType::curved, juce::PathStrokeType::rounded));

    if (amount <= 0.0f)
        return;

    juce::Path value;
    value.addCentredArc(bounds.getCentreX(), bounds.getCentreY(), radius, radius,
                        0.0f, start, start + (end - start) * juce::jlimit(0.0f, 1.0f, amount), true);
    g.setColour(accent.withAlpha(0.20f));
    g.strokePath(value, juce::PathStrokeType(thickness + 5.0f,
                 juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
    g.setColour(accent);
    g.strokePath(value, juce::PathStrokeType(thickness,
                 juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
}

void AifredAudioProcessorEditor::drawMetricValue(juce::Graphics& g,
                                                  juce::Rectangle<float> bounds,
                                                  const DisplayMetric& metric,
                                                  juce::StringRef unit,
                                                  int decimals,
                                                  juce::Colour colour) const
{
    g.setColour(metric.valid ? colour : textSecondary);
    g.setFont(makeFont(15.0f, juce::Font::bold));
    g.drawText(formattedValue(metric, unit, decimals), bounds, juce::Justification::centred);
}

juce::String AifredAudioProcessorEditor::currentFinding() const
{
    if (! latestSnapshot.hasSignal)
        return "NO SIGNAL";
    if (peak.valid && peak.target > -1.0f)
        return "VERY HIGH PEAK";
    if (correlation.valid && correlation.target < -0.10f)
        return "NEGATIVE CORRELATION";
    if (crest.valid && crest.target < 6.0f)
        return "LOW CREST / DENSE DYNAMICS";
    if (width.valid && width.target > 0.75f)
        return "VERY WIDE STEREO";

    const auto bandsValid = std::all_of(spectrum.begin(), spectrum.end(),
                                        [] (const DisplayMetric& band) { return band.valid; });
    if (bandsValid)
    {
        const auto bass = (spectrum[0].target + spectrum[1].target) * 0.5f;
        const auto treble = (spectrum[5].target + spectrum[6].target) * 0.5f;
        if (bass > treble + 6.0f)
            return "BASS-HEAVY";
        if (treble > bass + 6.0f)
            return "TREBLE-HEAVY";
    }

    return peak.valid ? "SIGNAL ACTIVE" : "ANALYZING";
}

float AifredAudioProcessorEditor::normalized(float value, float minimum,
                                              float maximum) noexcept
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
    if (unit.isNotEmpty())
    {
        value += " ";
        value += unit;
    }
    return value;
}
