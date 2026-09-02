#pragma once

#include <string_view>

#ifndef AIFRED_VERSION_STRING
#define AIFRED_VERSION_STRING "0.0.0-unknown"
#endif

#ifndef AIFRED_GIT_COMMIT
#define AIFRED_GIT_COMMIT "unknown"
#endif

#ifndef AIFRED_BUILD_CONFIGURATION
#define AIFRED_BUILD_CONFIGURATION "UNKNOWN"
#endif

#ifndef AIFRED_BUILD_PLATFORM
#define AIFRED_BUILD_PLATFORM "UNKNOWN"
#endif

#ifndef AIFRED_UPDATE_CHANNEL
#define AIFRED_UPDATE_CHANNEL "alpha"
#endif

namespace aifred::build
{
struct BuildIdentity final
{
    static constexpr std::string_view version { AIFRED_VERSION_STRING };
    static constexpr std::string_view commit { AIFRED_GIT_COMMIT };
    static constexpr std::string_view configuration { AIFRED_BUILD_CONFIGURATION };
    static constexpr std::string_view platform { AIFRED_BUILD_PLATFORM };
    static constexpr std::string_view updateChannel { AIFRED_UPDATE_CHANNEL };
};
} // namespace aifred::build
