// ============================================================
// serial_protocol.h — Serial JSON Command Parser
// ============================================================
// Non-blocking serial line reader + lightweight JSON parser.
// Commands:
//   {"cmd":"state","value":"thinking"}
//   {"cmd":"state","value":"working","subtype":"code"}
//   {"cmd":"state","value":"completed","summary":"Done!"}
//   {"cmd":"text","value":"正在分析..."}
//   {"cmd":"sleep"}
//   {"cmd":"wake"}
// ============================================================

#ifndef SERIAL_PROTOCOL_H
#define SERIAL_PROTOCOL_H

#include <Arduino.h>
#include "state_machine.h"

// ==================== SERIAL BUFFER ====================

#define SERIAL_BUF_SIZE 256
static char serial_buf[SERIAL_BUF_SIZE];
static uint8_t serial_idx = 0;

// ==================== LIGHTWEIGHT JSON PARSER ====================

// Extract string value for a given key: {"key":"value"}
// Returns pointer to value within buf (null-terminated), or NULL if not found
static char* jsonExtractStr(char* buf, const char* key) {
    char search[64];
    snprintf(search, sizeof(search), "\"%s\":\"", key);
    char* p = strstr(buf, search);
    if (!p) return NULL;
    p += strlen(search);
    char* end = strchr(p, '"');
    if (!end) return NULL;
    *end = '\0';
    return p;
}

// Extract integer value: {"key":123}
static int jsonExtractInt(char* buf, const char* key) {
    char search[64];
    snprintf(search, sizeof(search), "\"%s\":", key);
    char* p = strstr(buf, search);
    if (!p) return -1;
    p += strlen(search);
    return atoi(p);
}

// Extract float: {"key":0.5}
static float jsonExtractFloat(char* buf, const char* key) {
    char search[64];
    snprintf(search, sizeof(search), "\"%s\":", key);
    char* p = strstr(buf, search);
    if (!p) return -1;
    p += strlen(search);
    return atof(p);
}

// ==================== COMMAND PROCESSOR ====================

static void processSerialCommand(char* json) {
    // Extract "cmd" field
    char* cmd = jsonExtractStr(json, "cmd");
    if (!cmd) return;

    st.last_serial_ms = millis();
    st.last_active_ms = millis();
    st.ever_connected = true;  // Disable disconnect guard after first command

    // --- STATE CHANGE ---
    if (strcmp(cmd, "state") == 0) {
        char* value = jsonExtractStr(json, "value");
        if (!value) return;

        AgentState new_state = ST_IDLE;
        if (strcmp(value, "idle") == 0)      new_state = ST_IDLE;
        else if (strcmp(value, "thinking") == 0) new_state = ST_THINKING;
        else if (strcmp(value, "working") == 0)  new_state = ST_WORKING;
        else if (strcmp(value, "completed") == 0) new_state = ST_COMPLETED;
        else if (strcmp(value, "error") == 0) new_state = ST_ERROR;
        else return;

        // Extract optional subtype for working
        if (new_state == ST_WORKING) {
            char* subtype = jsonExtractStr(json, "subtype");
            if (subtype) {
                if (strcmp(subtype, "search") == 0)      st.work_subtype = WS_SEARCH;
                else if (strcmp(subtype, "code") == 0)   st.work_subtype = WS_CODE;
                else if (strcmp(subtype, "file") == 0)   st.work_subtype = WS_FILE;
                else if (strcmp(subtype, "api") == 0)    st.work_subtype = WS_API;
                else st.work_subtype = WS_DEFAULT;
            }
        }

        // Extract optional summary for completed
        if (new_state == ST_COMPLETED) {
            char* summary = jsonExtractStr(json, "summary");
            if (summary) {
                strncpy(st.summary_buf, summary, sizeof(st.summary_buf) - 1);
                st.text_dirty = true;
            }
        }

        transitionTo(new_state);
        Serial.println("{\"ack\":\"ok\"}");

    // --- TEXT UPDATE ---
    } else if (strcmp(cmd, "text") == 0) {
        char* text = jsonExtractStr(json, "value");
        if (text) {
            strncpy(st.text_buf, text, sizeof(st.text_buf) - 1);
            st.text_dirty = true;
            Serial.println("{\"ack\":\"ok\"}");
        }

    // --- SLEEP ---
    } else if (strcmp(cmd, "sleep") == 0) {
        transitionTo(ST_SLEEP);
        Serial.println("{\"ack\":\"ok\"}");

    // --- WAKE ---
    } else if (strcmp(cmd, "wake") == 0) {
        transitionTo(ST_IDLE);
        // Reset idle timer on wake
        st.idle_start_ms = millis();
        Serial.println("{\"ack\":\"ok\"}");

    } else {
        Serial.println("{\"ack\":\"error\",\"msg\":\"unknown_cmd\"}");
    }
}

// ==================== SERIAL READER (call in loop) ====================

static void serialPoll() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (serial_idx > 0) {
                serial_buf[serial_idx] = '\0';
                processSerialCommand(serial_buf);
                serial_idx = 0;
            }
        } else if (serial_idx < SERIAL_BUF_SIZE - 1) {
            serial_buf[serial_idx++] = c;
        }
    }
}

#endif
