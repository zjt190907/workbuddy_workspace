// ============================================================
// text_overlay.h — Text Bubble & Scrolling Display
// ============================================================
// Renders text messages in a bottom band (40px height).
// Supports: typewriter effect, auto-scroll, Chinese characters.
// ============================================================

#ifndef TEXT_OVERLAY_H
#define TEXT_OVERLAY_H

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include "state_machine.h"

// ==================== CONFIG ====================

#define TEXT_AREA_Y      195     // Top of text band (leaves 45px)
#define TEXT_AREA_H      42      // Text area height
#define TEXT_FONT_W      6       // Approximate char width (GFX size 1)
#define TEXT_FONT_H      8       // Approximate char height
#define TEXT_MAX_CHARS   40      // Max characters per line (240/6 ≈ 40)
#define TEXT_MAX_LINES   2       // Max visible lines
#define TEXT_SCROLL_STEP 2       // Pixels per scroll step
#define TEXT_SCROLL_MS   60      // Scroll speed (ms per step)
#define TEXT_COLOR       0xFFE0  // Warm yellow text
#define TEXT_BG         0x2104  // Background

// ==================== TEXT STATE ====================

struct TextState {
    char    lines[4][64];   // Up to 4 lines of text
    uint8_t num_lines;
    uint8_t scroll_line;    // Current line being "typed"
    uint8_t scroll_pos;     // Pixel scroll position
    uint8_t char_pos;       // Characters shown so far (typewriter)
    uint32_t last_tick;
    bool    active;
};

static TextState txt = {
    .lines       = {{0}},
    .num_lines   = 0,
    .scroll_line = 0,
    .scroll_pos  = 0,
    .char_pos    = 0,
    .last_tick   = 0,
    .active      = false,
};

// ==================== FUNCTIONS ====================

// Simple char copy into lines[4] — GFX size 1 font is ASCII only
static void wrapText(const char* src) {
    memset(txt.lines, 0, sizeof(txt.lines));
    txt.num_lines = 0;
    txt.char_pos = 0;
    txt.scroll_line = 0;
    txt.scroll_pos = 0;
    txt.last_tick = millis();
    txt.active = (src[0] != '\0');

    if (!txt.active) return;

    int li = 0, ci = 0;
    while (*src && li < 4) {
        if (ci >= TEXT_MAX_CHARS - 1) {
            txt.lines[li][ci] = '\0';
            li++; ci = 0;
            if (li >= 4) break;
        }
        txt.lines[li][ci++] = *src++;
    }
    txt.lines[li][ci] = '\0';
    txt.num_lines = li + 1;
}

// Clear text area
static void clearTextArea(Adafruit_ST7789& tft) {
    tft.fillRect(0, TEXT_AREA_Y, 240, TEXT_AREA_H, TEXT_BG);
    // Subtle separator line
    tft.drawFastHLine(10, TEXT_AREA_Y, 220, 0x4228);
}

// Draw current text state (typewriter + scroll)
static void drawTextOverlay(Adafruit_ST7789& tft) {
    if (!txt.active) return;

    uint32_t now = millis();

    // Typewriter advance
    if (txt.char_pos < strlen(txt.lines[txt.scroll_line])) {
        if (now - txt.last_tick >= 50) {  // 50ms per char
            txt.char_pos++;
            txt.last_tick = now;
        }
    }

    // Draw background
    clearTextArea(tft);

    tft.setTextSize(1);
    tft.setTextColor(TEXT_COLOR, TEXT_BG);
    tft.setTextWrap(false);

    // Draw visible lines from scroll_line
    for (int i = 0; i < min((int)txt.num_lines - txt.scroll_line, TEXT_MAX_LINES); i++) {
        int line_idx = txt.scroll_line + i;
        int y_pos = TEXT_AREA_Y + 4 + (TEXT_FONT_H + 2) * i - txt.scroll_pos;

        // Bounds check
        if (y_pos < TEXT_AREA_Y - TEXT_FONT_H || y_pos > TEXT_AREA_Y + TEXT_AREA_H) continue;

        char line_display[64];
        int show_len = txt.char_pos;
        if (line_idx > (int)txt.scroll_line) show_len = strlen(txt.lines[line_idx]);
        if (line_idx == (int)txt.scroll_line) {
            show_len = txt.char_pos;
        }

        strncpy(line_display, txt.lines[line_idx], show_len);
        line_display[show_len] = '\0';

        // Center text
        int pixel_w = show_len * TEXT_FONT_W;
        int x_start = max(4, (240 - pixel_w) / 2);

        tft.setCursor(x_start, y_pos);
        tft.print(line_display);

        // Cursor blink (underline at end of current line)
        if (line_idx == (int)txt.scroll_line && (now % 800) < 400) {
            int cursor_x = x_start + pixel_w;
            tft.drawFastVLine(cursor_x, y_pos + 1, TEXT_FONT_H, TEXT_COLOR);
        }
    }
}

// Update text when new content arrives
static void updateTextContent(const char* new_text) {
    wrapText(new_text);
}

#endif
