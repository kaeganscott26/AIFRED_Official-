#pragma once

#include <juce_core/juce_core.h>

#include "ReferenceClient.h"
#include "core/analysis/ComparisonEngine.h"

namespace aifred::services
{
enum class ConversationMode
{
    analyze,
    compare,
    reference
};

struct ConversationContextInput final
{
    ConversationMode mode = ConversationMode::analyze;
    double sampleRate = 0.0;
    const analysis::AnalysisSnapshot* current = nullptr;
    const analysis::SnapshotCaptureModel* captures = nullptr;
    const ReferenceProfile* reference = nullptr;
};

[[nodiscard]] juce::var buildConversationContext(
    const ConversationContextInput& input);
[[nodiscard]] juce::String serializeConversationContext(
    const ConversationContextInput& input);
} // namespace aifred::services
