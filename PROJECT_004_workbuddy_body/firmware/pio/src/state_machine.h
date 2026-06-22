// ============================================================
// state_machine.h — Agent State Machine
// ============================================================
// Defines all states, transitions, and timing rules.
// ============================================================

#ifndef STATE_MACHINE_H
#define STATE_MACHINE_H

#include <Arduino.h>

// ==================== STATES ====================

enum AgentState {
    ST_IDLE = 0,
    ST_THINKING,
    ST_WORKING,
    ST_COMPLETED,
    ST_SLEEP,
    ST_ERROR,
    ST_DISCONNECTED,
    ST_COUNT
};

// Working subtypes
enum WorkSubtype {
    WS_DEFAULT = 0,
    WS_SEARCH,    // 搜索网络
    WS_CODE,      // 执行代码
    WS_FILE,      // 读取文件
    WS_API        // API 调用
};

// ==================== STATE DATA ====================

struct StateData {
    AgentState   state;
    AgentState   prev_state;
    WorkSubtype  work_subtype;
    uint32_t     state_start_ms;
    uint32_t     last_active_ms;   // Last time PC sent any command
    uint32_t     idle_start_ms;    // When idle mode started
    char         text_buf[128];    // Current text message from PC
    char         summary_buf[64];  // Completion summary
    bool         text_dirty;       // New text received, needs redraw
    bool         transitioning;    // Mid-transition animation
    uint32_t     trans_start_ms;

    // Idle phrases
    uint8_t      idle_phrase_idx;

    // Expression variant (randomized per state entry)
    uint8_t      expr_variant;

    // Backlight breathing
    uint8_t      bl_brightness;    // 0-255
    bool         bl_breathing;

    // Disconnect watchdog
    uint32_t     last_serial_ms;
    uint32_t     last_wifi_ms;
    bool         ever_connected;    // Only detect disconnect after first connection
};

// ==================== STATE MACHINE ====================

static StateData st = {
    .state          = ST_IDLE,
    .prev_state     = ST_IDLE,
    .work_subtype   = WS_DEFAULT,
    .state_start_ms = 0,
    .last_active_ms = 0,
    .idle_start_ms  = 0,
    .text_buf       = {0},
    .summary_buf    = {0},
    .text_dirty     = false,
    .transitioning  = false,
    .trans_start_ms = 0,
    .idle_phrase_idx = 0,
    .expr_variant   = 0,
    .bl_brightness  = 255,
    .bl_breathing   = false,
    .last_serial_ms = 0,
    .last_wifi_ms   = 0,
    .ever_connected = false,
};

// ==================== STATE HELPERS ====================

static const char* stateName(AgentState s) {
    switch (s) {
        case ST_IDLE:        return "idle";
        case ST_THINKING:    return "thinking";
        case ST_WORKING:     return "working";
        case ST_COMPLETED:   return "completed";
        case ST_SLEEP:       return "sleep";
        case ST_ERROR:       return "error";
        case ST_DISCONNECTED:return "disconnected";
        default:             return "unknown";
    }
}

static const char* workSubtypeName(WorkSubtype ws) {
    switch (ws) {
        case WS_SEARCH: return "search";
        case WS_CODE:   return "code";
        case WS_FILE:   return "file";
        case WS_API:    return "api";
        default:        return "default";
    }
}

// Transition to a new state (with animation trigger)
static void transitionTo(AgentState new_state) {
    st.prev_state    = st.state;
    st.state         = new_state;
    st.state_start_ms= millis();
    st.trans_start_ms = millis();
    st.transitioning = true;
    st.text_dirty    = false;
    st.idle_start_ms = (new_state == ST_IDLE) ? millis() : 0;

    // Random expression variant on entry
    st.expr_variant = random(3);  // 0, 1, or 2 variants

    // Reset text unless thinking/working with text
    if (new_state != ST_THINKING && new_state != ST_WORKING) {
        memset(st.text_buf, 0, sizeof(st.text_buf));
    }
}

// Idle timeout → auto-sleep
#define IDLE_SLEEP_TIMEOUT_MS  120000  // 2 minutes idle → sleep

// Completed auto-return
#define COMPLETED_DISPLAY_MS   4000    // Show completion for 4 seconds

// Disconnect timeout
#define DISCONNECT_TIMEOUT_MS  8000    // 8s no comm → disconnected face

#endif
