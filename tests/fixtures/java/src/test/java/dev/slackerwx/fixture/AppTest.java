package dev.slackerwx.fixture;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AppTest {
    @Test
    void healthBodyIsJson() {
        assertEquals("{\"ok\":true}", App.body("/health"));
        assertEquals("application/json", App.contentType("/health"));
    }
}
