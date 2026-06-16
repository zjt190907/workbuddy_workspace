// ============================================================
// WorkBuddy Body — Sprite Renderer
// ============================================================
// Draws sprite frames from PROGMEM arrays onto ST7789 display.
// ============================================================

#include <Adafruit_ST7789.h>
#include <pgmspace.h>
#include "sprites.h"
#include "expressions.h"

// ==================== SPRITE TABLE ====================

const Sprite sprite_sets[SPR_COUNT] = {
    { sprite_error_0, 3 },
    { sprite_happy_0, 3 },
    { sprite_idle_0, 3 },
    { sprite_sleeping_0, 3 },
    { sprite_thinking_0, 3 },
    { sprite_working_0, 2 },
};

const char* getSpriteName(SpriteSet s) {
    switch (s) {
        case SPR_ERROR:    return "error";
        case SPR_HAPPY:    return "happy";
        case SPR_IDLE:     return "idle";
        case SPR_SLEEPING: return "sleeping";
        case SPR_THINKING: return "thinking";
        case SPR_WORKING:  return "working";
        default:           return "unknown";
    }
}

SpriteSet getSpriteByName(const String& name) {
    if (name == "error")    return SPR_ERROR;
    if (name == "happy")    return SPR_HAPPY;
    if (name == "idle")     return SPR_IDLE;
    if (name == "sleeping") return SPR_SLEEPING;
    if (name == "thinking") return SPR_THINKING;
    if (name == "working")  return SPR_WORKING;
    return SPR_INVALID;
}

// ==================== PROGMEM SPRITE DRAW ====================

void drawSpriteFrame(Adafruit_ST7789& tft, SpriteSet s, uint8_t frame,
                     int16_t ox=0, int16_t oy=0) {
    if (s < 0 || s >= SPR_COUNT) return;
    if (frame >= sprite_sets[s].num_frames) frame %= sprite_sets[s].num_frames;

    int16_t sx = (240 - SPRITE_W) / 2 + ox;
    int16_t sy = (240 - SPRITE_H) / 2 + oy;

    uint16_t frame_offset = frame * (uint16_t)SPRITE_W * SPRITE_H * 2;
    const uint8_t* data = sprite_sets[s].data + frame_offset;

    tft.startWrite();
    tft.setAddrWindow(sx, sy, sx + SPRITE_W - 1, sy + SPRITE_H - 1);

    uint16_t idx = 0;
    for (int16_t y = 0; y < SPRITE_H; y++) {
        for (int16_t x = 0; x < SPRITE_W; x++) {
            uint16_t color = ((uint16_t)pgm_read_byte(&data[idx]) << 8)
                           |  (uint16_t)pgm_read_byte(&data[idx + 1]);
            idx += 2;
            tft.writePixel(x, y, color);
        }
    }
    tft.endWrite();
}

// ==================== EXPRESSION MAPPING ====================

SpriteSet exprToSprite(Expression ex) {
    switch (ex) {
        case EXPR_IDLE:     return SPR_IDLE;
        case EXPR_HAPPY:    return SPR_HAPPY;
        case EXPR_THINKING: return SPR_THINKING;
        case EXPR_WORKING:  return SPR_WORKING;
        case EXPR_SLEEPING: return SPR_SLEEPING;
        case EXPR_ERROR:    return SPR_ERROR;
        default:            return SPR_INVALID;
    }
}

static uint8_t  sprite_frame[EXPR_COUNT] = {0};
static uint32_t sprite_timer[EXPR_COUNT] = {0};

void drawExpressionSprite(Adafruit_ST7789& tft, AnimState& st) {
    SpriteSet s = exprToSprite(st.current);
    if (s == SPR_INVALID) return;

    uint32_t now = millis();
    uint32_t interval = (4 - st.speed) * 160;
    if (now - sprite_timer[st.current] >= interval) {
        sprite_frame[st.current]++;
        sprite_timer[st.current] = now;
    }
    uint8_t frame = sprite_frame[st.current] % sprite_sets[s].num_frames;

    tft.fillScreen(st.bg_color);
    drawSpriteFrame(tft, s, frame);
}
