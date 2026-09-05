cmake_minimum_required(VERSION 3.22)

project(AIFRED VERSION 4.0.0 LANGUAGES C CXX)

set(AIFRED_VERSION_STRING "4.0.0-alpha.2" CACHE STRING "Visible AIFRED product version")
set(AIFRED_UPDATE_CHANNEL "alpha" CACHE STRING "AIFRED update channel")
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

set(AIFRED_COMPARISON_SOURCES plugin/src/CaptureComparison.cpp)
set(AIFRED_INTEGRATION_SOURCES plugin/src/ReferenceClient.cpp)
enable_testing()
add_subdirectory(shared-dsp)

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
        AIFRED_REFERENCE_API_URL="${AIFRED_REFERENCE_API_URL}"
)

target_link_libraries(Aifred
    PRIVATE
        juce::juce_audio_utils
        juce::juce_dsp
        juce::juce_gui_extra
        AifredVisualizationAssets
        aifred_pipeline
    PUBLIC
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)



add_executable(aifred_frontend_contract_tests tests/frontend_contract_tests.cpp)
target_include_directories(aifred_frontend_contract_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(aifred_frontend_contract_tests PRIVATE aifred_pipeline)
add_test(NAME aifred_frontend_contract_tests COMMAND aifred_frontend_contract_tests)

add_executable(aifred_state_contract_tests tests/state_contract_tests.cpp)
target_include_directories(aifred_state_contract_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_BINARY_DIR}/_deps/juce-src/modules)
target_compile_definitions(aifred_state_contract_tests PRIVATE JUCE_GLOBAL_MODULE_SETTINGS_INCLUDED=1)
target_link_libraries(aifred_state_contract_tests PRIVATE Aifred aifred_pipeline)
add_test(NAME aifred_state_contract_tests COMMAND aifred_state_contract_tests)
