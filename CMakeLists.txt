cmake_minimum_required(VERSION 3.22)

project(AIFRED VERSION 4.0.0 LANGUAGES C CXX)

set(AIFRED_VERSION_STRING "4.0.0-alpha.2" CACHE STRING "Visible AIFRED product version")
set(AIFRED_UPDATE_CHANNEL "alpha" CACHE STRING "AIFRED update channel")
set(AIFRED_ENGINE_URL "http://127.0.0.1:8787" CACHE STRING "Local AifredEngine origin")
set(AIFRED_REFERENCE_API_URL "https://www.north3rnlight3r.com/api/v1/references" CACHE STRING "Production reference catalog URL")

execute_process(
    COMMAND git rev-parse --short=7 HEAD
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    OUTPUT_VARIABLE AIFRED_GIT_COMMIT
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)
if(NOT AIFRED_GIT_COMMIT)
    set(AIFRED_GIT_COMMIT "unknown")
endif()

if(WIN32 AND CMAKE_SIZEOF_VOID_P EQUAL 8)
    set(AIFRED_BUILD_PLATFORM "WIN64")
elseif(WIN32)
    set(AIFRED_BUILD_PLATFORM "WIN32")
elseif(APPLE)
    set(AIFRED_BUILD_PLATFORM "MACOS")
else()
    set(AIFRED_BUILD_PLATFORM "LINUX")
endif()

if(CMAKE_BUILD_TYPE)
    string(TOUPPER "${CMAKE_BUILD_TYPE}" AIFRED_BUILD_CONFIGURATION)
else()
    set(AIFRED_BUILD_CONFIGURATION "MULTI-CONFIG")
endif()

message(STATUS "AIFRED ${AIFRED_VERSION_STRING} (${AIFRED_GIT_COMMIT}) ${AIFRED_BUILD_PLATFORM} / ${AIFRED_BUILD_CONFIGURATION}")

include(FetchContent)

set(FETCHCONTENT_QUIET OFF)
FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 8.0.8
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(JUCE)

if(WIN32)
    # Pin the build-time WebView2 SDK so developers do not depend on a random
    # machine-local NuGet cache. The runtime visualizer remains fully offline.
    FetchContent_Declare(
        AifredWebView2
        URL https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/1.0.1901.177
        URL_HASH SHA256=464360D5EEDCAE0E95B0A3FE13C74B496BC9B542980FF8ECEBD9FF7EA37CA39E
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
        SOURCE_DIR "${CMAKE_BINARY_DIR}/_deps/Microsoft.Web.WebView2-1.0.1901.177"
    )
    FetchContent_MakeAvailable(AifredWebView2)
    set(JUCE_WEBVIEW2_PACKAGE_LOCATION "${CMAKE_BINARY_DIR}/_deps")
endif()

juce_add_binary_data(AifredVisualizationAssets
    HEADER_NAME AifredVisualizationAssets.h
    NAMESPACE AifredVisualizationAssets
    SOURCES
        plugin/visualization/index.html
        plugin/visualization/visualizer.css
        plugin/visualization/visualizer.js
        plugin/visualization/three.module.min.js
)

set(AIFRED_DSP_SOURCES
    core/analysis/AnalysisCoordinator.cpp
    core/dsp/LevelAnalyzer.cpp
    core/dsp/LoudnessAnalyzer.cpp
    core/dsp/SpectrumAnalyzer.cpp
    core/dsp/StereoAnalyzer.cpp
)

set(AIFRED_COMPARISON_SOURCES
    core/analysis/ComparisonEngine.cpp
)

set(AIFRED_INTEGRATION_SOURCES
    plugin/src/AifredEngineClient.cpp
    plugin/src/AnalysisContextSerializer.cpp
    plugin/src/ReferenceClient.cpp
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
    NEEDS_WEB_BROWSER TRUE
    NEEDS_WEBVIEW2 TRUE
)

# Plugin sources use JUCE's conventional aggregate header. Keep it generated
# by JUCE so it exactly matches the linked module set on every platform.
juce_generate_juce_header(Aifred)

target_sources(Aifred PRIVATE
    plugin/src/PluginProcessor.cpp
    plugin/src/PluginEditor.cpp
    ${AIFRED_DSP_SOURCES}
    ${AIFRED_COMPARISON_SOURCES}
    ${AIFRED_INTEGRATION_SOURCES}
)

target_include_directories(Aifred PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(Aifred PRIVATE cxx_std_20)
target_compile_definitions(Aifred
    PUBLIC
        JUCE_WEB_BROWSER=1
        JUCE_USE_CURL=0
        JUCE_VST3_CAN_REPLACE_VST2=0
    PRIVATE
        AIFRED_VERSION_STRING="${AIFRED_VERSION_STRING}"
        AIFRED_GIT_COMMIT="${AIFRED_GIT_COMMIT}"
        AIFRED_BUILD_CONFIGURATION="${AIFRED_BUILD_CONFIGURATION}"
        AIFRED_BUILD_PLATFORM="${AIFRED_BUILD_PLATFORM}"
        AIFRED_UPDATE_CHANNEL="${AIFRED_UPDATE_CHANNEL}"
        AIFRED_ENGINE_URL="${AIFRED_ENGINE_URL}"
        AIFRED_REFERENCE_API_URL="${AIFRED_REFERENCE_API_URL}"
)

target_link_libraries(Aifred
    PRIVATE
        juce::juce_audio_utils
        juce::juce_dsp
        juce::juce_gui_extra
        AifredVisualizationAssets
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

add_executable(aifred_comparison_tests
    tests/comparison_engine_tests.cpp
    ${AIFRED_COMPARISON_SOURCES}
)
target_include_directories(aifred_comparison_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(aifred_comparison_tests PRIVATE cxx_std_20)

add_executable(aifred_integration_contract_tests
    tests/integration_contract_tests.cpp
    ${AIFRED_INTEGRATION_SOURCES}
    ${AIFRED_COMPARISON_SOURCES}
)
target_include_directories(aifred_integration_contract_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(aifred_integration_contract_tests PRIVATE cxx_std_20)
target_compile_definitions(aifred_integration_contract_tests PRIVATE
    JUCE_WEB_BROWSER=0
    JUCE_USE_CURL=0
    AIFRED_ENGINE_URL="${AIFRED_ENGINE_URL}"
    AIFRED_REFERENCE_API_URL="${AIFRED_REFERENCE_API_URL}"
)
target_link_libraries(aifred_integration_contract_tests PRIVATE
    juce::juce_core
    juce::juce_recommended_config_flags
    juce::juce_recommended_warning_flags
)

enable_testing()
add_test(NAME aifred_dsp_smoke COMMAND aifred_dsp_smoke)
add_test(NAME aifred_comparison_tests COMMAND aifred_comparison_tests)
add_test(NAME aifred_integration_contract_tests COMMAND aifred_integration_contract_tests)
