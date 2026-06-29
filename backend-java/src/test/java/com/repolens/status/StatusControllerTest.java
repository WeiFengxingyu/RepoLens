package com.repolens.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.equalTo;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class StatusControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void healthReturnsOk() throws Exception {
        mockMvc.perform(get("/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", equalTo("ok")));
    }

    @Test
    void statusReturnsServiceMetadata() throws Exception {
        mockMvc.perform(get("/api/status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.service", equalTo("repolens-java")))
                .andExpect(jsonPath("$.version", equalTo("v1")))
                .andExpect(jsonPath("$.status", equalTo("ok")))
                .andExpect(jsonPath("$.storage.database", equalTo("not_configured")))
                .andExpect(jsonPath("$.storage.workspaceRoot", equalTo("./.repolens-java/repos")))
                .andExpect(jsonPath("$.storage.indexRoot", equalTo("./.repolens-java/indexes")));
    }
}
