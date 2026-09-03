#include "plugin/src/AifredEngineClient.h"
#include "plugin/src/AnalysisContextSerializer.h"
#include "plugin/src/ReferenceClient.h"

#include <cmath>
#include <cstdlib>
#include <iostream>
#include <string>

namespace
{
struct Test final
{
    int failures = 0;
    void expect(bool condition, const std::string& message)
    {
        if (condition)
            return;
        ++failures;
        std::cerr << "FAIL: " << message << '\n';
    }
};

aifred::analysis::AnalysisSnapshot snapshot(double gainDb)
{
    using aifred::analysis::MetricValue;
    aifred::analysis::AnalysisSnapshot value;
    value.sequence = gainDb == 0.0 ? 10 : 20;
    value.audioSampleClock = 48000;
    value.elapsedSeconds = 1.0;
    value.hasSignal = true;
    value.samplePeakDbfs = { -12.0 + gainDb, true };
    value.rmsDbfs = { -15.0 + gainDb, true };
    value.crestDb = { 3.0, true };
    value.shortTermLufs = { -16.0 + gainDb, true };
    value.width = { 0.4, true };
    value.correlation = { 0.8, true };
    value.spectrumBinWidthHz = { 48000.0 / 2048.0, true };
    for (std::size_t index = 1; index < value.spectrumBins.size(); ++index)
        value.spectrumBins[index] = MetricValue { -60.0 + gainDb, true };
    return value;
}

const juce::var property(const juce::var& object, const char* name)
{
    return object.getProperty(name, {});
}
} // namespace

int main()
{
    using namespace aifred;
    Test test;

    const auto catalog = services::parseReferenceCatalog(R"json({
      "contract_version":"aifred.references.v1",
      "available":true,
      "references":[
        {"available":true,"id":"zero","name":"Zero is valid","version":"test.v1",
         "metrics":{"sample_peak_dbfs":{"available":true,"value":0},
                    "rms_dbfs":{"available":false,"value":-90},
                    "crest_db":{"available":true,"value":12.5},
                    "spectrum_band_dbfs":[{"available":false,"value":-99}]}},
        {"available":true,"id":"path","name":"C:\\private\\Reference.wav","version":"test.v1","metrics":{}}
      ]
    })json");
    test.expect(catalog.status == services::ReferenceCatalogStatus::available
                    && catalog.references.size() == 2,
                "reference parser must preserve the production list contract");
    test.expect(catalog.references[0].metrics.samplePeakDbfs.valid
                    && catalog.references[0].metrics.samplePeakDbfs.value == 0.0,
                "a measured zero must remain a valid zero");
    test.expect(! catalog.references[0].metrics.rmsDbfs.valid
                    && ! catalog.references[0].metrics.legacySpectrumBandDbfs[0].valid,
                "explicitly unavailable reference metrics must not become sentinels");
    test.expect(catalog.references[1].name == "Reference.wav",
                "reference display identity must not expose a private path");

    const auto unavailable = services::parseReferenceCatalog(R"json({
      "contract_version":"aifred.references.v1","available":false,
      "reason":"no_usable_references","reference":null,"references":[]
    })json");
    test.expect(unavailable.status == services::ReferenceCatalogStatus::unavailable
                    && unavailable.references.empty(),
                "missing production references must remain explicitly unavailable");

    const auto current = snapshot(0.0);
    services::ConversationContextInput analyzeInput;
    analyzeInput.mode = services::ConversationMode::analyze;
    analyzeInput.sampleRate = 48000.0;
    analyzeInput.current = &current;
    const auto analyzeJson = services::serializeConversationContext(analyzeInput);
    const auto analyze = juce::JSON::parse(analyzeJson);
    test.expect(property(analyze, "mode").toString() == "Analyze"
                    && property(analyze, "current").isObject(),
                "Analyze context must contain the current mix");
    test.expect(property(analyze, "mix_a").isVoid()
                    && property(analyze, "reference").isVoid(),
                "Analyze context must not inject Compare or Reference state");
    test.expect(analyzeJson.contains("mean_fft_bin_power_dbfs")
                    && ! analyzeJson.contains("C:\\")
                    && ! analyzeJson.containsIgnoreCase("api_key"),
                "Analyze context must be compact and privacy safe");

    analysis::SnapshotCaptureModel captures;
    captures.captureA(current);
    captures.captureB(snapshot(6.0));
    services::ConversationContextInput compareInput;
    compareInput.mode = services::ConversationMode::compare;
    compareInput.sampleRate = 48000.0;
    compareInput.captures = &captures;
    const auto compare = juce::JSON::parse(
        services::serializeConversationContext(compareInput));
    test.expect(property(compare, "mix_a").isObject()
                    && property(compare, "mix_b").isObject()
                    && property(compare, "delta").isObject(),
                "Compare context must preserve Mix A, Mix B, and deltas");
    test.expect(property(compare, "reference").isVoid(),
                "Compare context must not call B a reference or inject reference data");
    const auto deltaMetrics = property(property(compare, "delta"), "metrics");
    const auto peakDelta = property(property(deltaMetrics, "sample_peak_dbfs"), "value");
    test.expect(std::abs(static_cast<double>(peakDelta) - 6.0) < 1.0e-9,
                "Compare context must preserve the factual B-minus-A peak delta");

    services::ConversationContextInput referenceInput;
    referenceInput.mode = services::ConversationMode::reference;
    referenceInput.sampleRate = 48000.0;
    referenceInput.current = &current;
    referenceInput.reference = &catalog.references[0];
    const auto referenceJson = services::serializeConversationContext(referenceInput);
    const auto reference = juce::JSON::parse(referenceJson);
    test.expect(property(reference, "current").isObject()
                    && property(reference, "reference").isObject()
                    && property(reference, "delta").isObject(),
                "Reference context must preserve current, selected reference, and compatible deltas");
    test.expect(referenceJson.contains("legacy_nine_band_dbfs")
                    && ! referenceJson.contains("C:\\private"),
                "Reference context must preserve available legacy resolution without private paths");

    const juce::String question = "Why does my chorus feel wider but weaker?";
    const auto requestJson = services::makeChatRequestJson(question, analyzeJson);
    const auto request = juce::JSON::parse(requestJson);
    test.expect(property(request, "message").toString() == question,
                "chat request must pass an arbitrary user question through unchanged");
    test.expect(property(request, "context").isObject(),
                "chat request must accompany the question with factual context");

    const auto backendDown = services::parseEngineHealth({}, 0);
    test.expect(! backendDown.backendAvailable && ! backendDown.providerAvailable,
                "backend absence must produce a clean unavailable state");
    const auto providerDown = services::parseEngineHealth(R"json({
      "engine_running":true,"provider":"ollama","model_name":"aifred:latest",
      "provider_ready":false,"last_error":"Ollama is unavailable."
    })json", 200);
    test.expect(providerDown.backendAvailable && ! providerDown.providerAvailable,
                "provider absence must not be reported as plugin or engine absence");

    if (test.failures == 0)
    {
        std::cout << "AIFRED integration contracts: PASS\n";
        return EXIT_SUCCESS;
    }
    std::cerr << "AIFRED integration contracts: " << test.failures << " failure(s)\n";
    return EXIT_FAILURE;
}
