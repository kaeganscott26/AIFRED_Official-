package com.aifred.admin

import org.junit.Assert.assertEquals
import org.junit.Test

class ApiConfigurationTest {
    @Test
    fun providerProfilesSelectExpectedEndpointsAndModels() {
        val website = apiProviderDefaults("website", "https://north3rnlight3r.com/api/")
        val ollama = apiProviderDefaults("ollama", website.baseUrl)
        val openai = apiProviderDefaults("openai", website.baseUrl, "private-key")

        assertEquals("https://north3rnlight3r.com", website.baseUrl)
        assertEquals("http://127.0.0.1:11434", ollama.baseUrl)
        assertEquals("aifred:latest", ollama.model)
        assertEquals("https://api.openai.com/v1", openai.baseUrl)
        assertEquals("gpt-5.6-luna", openai.model)
        assertEquals("private-key", openai.apiKey)
    }

    @Test
    fun legacyWebsiteBasesNormalizeToOneOrigin() {
        val expected = "https://north3rnlight3r.com"
        assertEquals(expected, normalizeWebsiteOrigin(expected))
        assertEquals(expected, normalizeWebsiteOrigin("$expected/api"))
        assertEquals(expected, normalizeWebsiteOrigin("$expected/api/v1"))
        assertEquals(expected, normalizeWebsiteOrigin("$expected/v1"))
    }

    @Test
    fun cleartextIsLimitedToLocalOrPrivateOllamaEndpoints() {
        assertEquals(null, validateApiEndpoint("http://127.0.0.1:11434"))
        assertEquals(null, validateApiEndpoint("http://192.168.1.20:11434"))
        assertEquals(null, validateApiEndpoint("http://172.16.0.2:11434"))
        assertEquals(null, validateApiEndpoint("https://ollama.example.com"))
        assertEquals(
            "Cleartext HTTP is limited to loopback/private-network API endpoints",
            validateApiEndpoint("http://ollama.example.com")
        )
    }
}
