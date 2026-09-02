cmake_minimum_required(VERSION 3.22)

project(AIFRED VERSION 4.0.0 LANGUAGES CXX)

include(FetchContent)

set(FETCHCONTENT_QUIET OFF)
FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 8.0.8
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(JUCE)

set(AIFRED_DSP_SOURCES
    core/analysis/AnalysisCoordinator.cpp
    core/dsp/LevelAnalyzer.cpp
    core/dsp/LoudnessAnalyzer.cpp
    core/dsp/SpectrumAnalyzer.cpp
    core/dsp/StereoAnalyzer.cpp
)

juce_add_plugin(Aifred
    COMPANY_NAME "AIFRED"
    BUNDLE_ID "com.aifred.audio.aifred"
    PLUGIN_MANUFACTURER_CODE Aifr
    PLUGIN_CODE Af40
    FORMATS VST3
    PRODUCT_NAME "Aifred"
    DESCRIPTION "AIFRED 4.0 Mix Intelligence Engine"
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE
)

# Plugin sources use JUCE's conventional aggregate header. Keep it generated
# by JUCE so it exactly matches the linked module set on every platform.
juce_generate_juce_header(Aifred)

target_sources(Aifred PRIVATE
    plugin/src/PluginProcessor.cpp
    plugin/src/PluginEditor.cpp
    ${AIFRED_DSP_SOURCES}
)

target_include_directories(Aifred PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(Aifred PRIVATE cxx_std_20)
target_compile_definitions(Aifred
    PUBLIC
        JUCE_WEB_BROWSER=0
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
    PRIVATE
        AIFRED_VERSION_STRING="4.0.0-alpha.1"
)

target_link_libraries(Aifred
    PRIVATE
        juce::juce_audio_utils
        juce::juce_dsp
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)

add_executable(aifred_dsp_smoke
    tests/dsp_smoke.cpp
    ${AIFRED_DSP_SOURCES}
)

target_include_directories(aifred_dsp_smoke PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(aifred_dsp_smoke PRIVATE cxx_std_20)
target_compile_definitions(aifred_dsp_smoke PRIVATE JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0)
target_link_libraries(aifred_dsp_smoke
    PRIVATE
        juce::juce_audio_basics
        juce::juce_core
        juce::juce_dsp
        juce::juce_recommended_config_flags
        juce::juce_recommended_warning_flags
)

enable_testing()
add_test(NAME aifred_dsp_smoke COMMAND aifred_dsp_smoke)
