// ============================================================
// expressions_v2.h — Rich Face Animation Engine
// ============================================================
// Geometry-based face expressions with multiple variants,
// particle effects, and smooth state transitions.
// ============================================================

#ifndef EXPRESSIONS_V2_H
#define EXPRESSIONS_V2_H

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include "state_machine.h"

// ==================== LAYOUT (160x160 face) ====================

#define FACE_CX         120
#define FACE_CY         95
#define EYE_W           24
#define EYE_H           40
#define EYE_GAP         50
#define EYE_R           5
#define L_EYE_X         (FACE_CX - EYE_GAP/2 - EYE_W/2)
#define R_EYE_X         (FACE_CX + EYE_GAP/2 + EYE_W/2)
#define EYE_Y           (FACE_CY - 8)
#define MOUTH_Y         (FACE_CY + 35)

// ==================== COLORS ====================

#define C_BG            0x2104
#define C_EYE           0xFBE0
#define C_MOUTH         0xFBE0
#define C_ERROR         0xF800
#define C_SLEEP         0x7BEF
#define C_DONE          0xFFE0  // Gold
#define C_SPARKLE       0xFFFF  // White sparkle
#define C_PARTICLE      0xFC00  // Orange particle
#define C_BLUSH         0xF9A6

// ==================== PARTICLES ====================

struct Particle {
    float x, y, vx, vy;
    uint8_t life;
    uint16_t color;
};

#define MAX_PARTICLES 30
static Particle particles[MAX_PARTICLES];
static uint8_t particle_count = 0;

static void spawnParticles(uint8_t count, int16_t cx, int16_t cy) {
    particle_count = min((int)count, MAX_PARTICLES);
    for (uint8_t i = 0; i < particle_count; i++) {
        particles[i].x = cx + random(-30, 30);
        particles[i].y = cy + random(-20, 20);
        float angle = random(-314, 314) / 100.0f;
        float speed = random(10, 40) / 10.0f;
        particles[i].vx = cos(angle) * speed;
        particles[i].vy = sin(angle) * speed - 0.5f;
        particles[i].life = random(20, 50);
        particles[i].color = (random(2) == 0) ? C_SPARKLE : C_PARTICLE;
    }
}

static void updateParticles(Adafruit_ST7789& tft) {
    for (uint8_t i = 0; i < particle_count; i++) {
        if (particles[i].life == 0) continue;
        // Erase old
        tft.fillCircle(particles[i].x, particles[i].y, 2, C_BG);
        // Update
        particles[i].x += particles[i].vx;
        particles[i].y += particles[i].vy;
        particles[i].vy += 0.08f;  // gravity
        particles[i].life--;
        // Draw new
        if (particles[i].life > 0) {
            tft.fillCircle(particles[i].x, particles[i].y, 2, particles[i].color);
        }
    }
}

// ==================== DRAWING HELPERS ====================

static void _rrect(Adafruit_ST7789& t, int16_t x, int16_t y,
    int16_t w, int16_t h, int16_t r, uint16_t c) {
    t.fillRoundRect(x - w/2, y - h/2, w, h, r, c);
}

static void _circle(Adafruit_ST7789& t, int16_t x, int16_t y,
    int16_t r, uint16_t c) {
    t.fillCircle(x, y, r, c);
}

// Draw eyes (used by multiple states)
static void drawEyePair(Adafruit_ST7789& tft, uint16_t col,
    int16_t lx, int16_t ly, int16_t rx, int16_t ry,
    int16_t w, int16_t h, bool closed = false) {
    if (closed) {
        tft.fillRect(lx - w/2, ly - 2, w, 4, col);
        tft.fillRect(rx - w/2, ry - 2, w, 4, col);
    } else {
        _rrect(tft, lx, ly, w, h, EYE_R, col);
        _rrect(tft, rx, ry, w, h, EYE_R, col);
    }
}

// ==================== IDLE STATE (3 variants) ====================

static void drawIdleV0(Adafruit_ST7789& tft, bool blink) {
    drawEyePair(tft, C_EYE, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W, EYE_H, blink);
    // Neutral mouth
    tft.fillRect(FACE_CX - 12, MOUTH_Y, 24, 3, C_MOUTH);
}

static void drawIdleV1(Adafruit_ST7789& tft, bool blink) {
    drawEyePair(tft, C_EYE, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W, EYE_H, blink);
    // Small smile
    tft.fillRect(FACE_CX - 10, MOUTH_Y + 2, 20, 2, C_MOUTH);
    tft.drawFastHLine(FACE_CX - 6, MOUTH_Y, 12, C_MOUTH);
    // Slight blush
    _circle(tft, L_EYE_X - 16, EYE_Y + 10, 5, C_BLUSH);
    _circle(tft, R_EYE_X + 16, EYE_Y + 10, 5, C_BLUSH);
}

static void drawIdleV2(Adafruit_ST7789& tft, bool blink) {
    int16_t lx = L_EYE_X + (blink ? 0 : (sin(millis()*0.002f) * 2));
    int16_t rx = R_EYE_X + (blink ? 0 : (sin(millis()*0.002f + 1) * 2));
    drawEyePair(tft, C_EYE, lx, EYE_Y, rx, EYE_Y, EYE_W, EYE_H, blink);
    // Thinking mouth (slightly offset)
    tft.fillRect(FACE_CX - 10, MOUTH_Y + 4, 20, 2, C_MOUTH);
}

// ==================== THINKING STATE (3 variants) ====================

static void drawThinkingV0(Adafruit_ST7789& tft) {
    // Left eye normal, right squinted
    _rrect(tft, L_EYE_X, EYE_Y, EYE_W, EYE_H - 8, EYE_R, C_EYE);
    tft.fillRect(R_EYE_X - EYE_W/2, EYE_Y, EYE_W, 5, C_EYE);
    // Eyes looking up
    _circle(tft, L_EYE_X, EYE_Y - 6, 6, 0x0000);
    // Question mark
    tft.setTextSize(1);
    tft.setTextColor(C_EYE);
    tft.setCursor(R_EYE_X + 18, EYE_Y - 20);
    tft.print("?");
    // Mouth
    tft.fillRect(FACE_CX - 8, MOUTH_Y + 2, 16, 2, C_MOUTH);
}

static void drawThinkingV1(Adafruit_ST7789& tft) {
    // Both eyes looking up-right
    _rrect(tft, L_EYE_X, EYE_Y - 2, EYE_W - 4, EYE_H - 4, EYE_R, C_EYE);
    _rrect(tft, R_EYE_X, EYE_Y - 2, EYE_W - 4, EYE_H - 4, EYE_R, C_EYE);
    // Pupils up-right
    _circle(tft, L_EYE_X + 4, EYE_Y - 10, 5, 0x0000);
    _circle(tft, R_EYE_X + 4, EYE_Y - 10, 5, 0x0000);
    // Dots animation (...)
    int dc = (millis() / 400) % 3 + 1;
    tft.setTextSize(1);
    tft.setTextColor(C_EYE);
    tft.setCursor(FACE_CX - 6, MOUTH_Y);
    for (int i = 0; i < dc; i++) tft.print(".");
}

static void drawThinkingV2(Adafruit_ST7789& tft) {
    // Hand scratching head
    drawEyePair(tft, C_EYE, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W - 4, EYE_H - 6, false);
    // Scratching hand (small arc on top-right)
    int ax = R_EYE_X + 20 + sin(millis()*0.01f)*3;
    int ay = EYE_Y - 30 + cos(millis()*0.01f)*3;
    _circle(tft, ax, ay, 6, C_EYE);
    // "Tilted" mouth
    tft.drawLine(FACE_CX - 10, MOUTH_Y, FACE_CX + 6, MOUTH_Y + 4, C_MOUTH);
    tft.drawLine(FACE_CX - 10, MOUTH_Y + 1, FACE_CX + 6, MOUTH_Y + 5, C_MOUTH);
}

// ==================== WORKING STATE (3 variants + 4 subtypes) ====================

static void drawWorkingGear(Adafruit_ST7789& tft, int16_t cx, int16_t cy, int r) {
    float angle = millis() * 0.003f;
    for (int i = 0; i < 6; i++) {
        float a = angle + i * 3.14159f * 2 / 6;
        int16_t x1 = cx + cos(a) * (r - 4);
        int16_t y1 = cy + sin(a) * (r - 4);
        int16_t x2 = cx + cos(a) * r;
        int16_t y2 = cy + sin(a) * r;
        tft.drawLine(x1, y1, x2, y2, C_EYE);
    }
    _circle(tft, cx, cy, r - 5, C_BG);
    _circle(tft, cx, cy, 3, C_EYE);
}

static void drawWorkingV0(Adafruit_ST7789& tft, WorkSubtype ws) {  // Focused eyes + gear
    drawEyePair(tft, C_EYE, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W, EYE_H - 10, false);
    drawWorkingGear(tft, R_EYE_X + 24, EYE_Y - 25, 10);
    // Subtype indicator
    tft.setTextSize(1);
    tft.setTextColor(C_EYE);
    if (ws == WS_SEARCH) {
        tft.setCursor(FACE_CX - 14, MOUTH_Y - 4);
        tft.print("(  )");  // magnifier
    } else if (ws == WS_CODE) {
        tft.setCursor(FACE_CX - 14, MOUTH_Y - 4);
        tft.print(">_");
    }
    tft.fillRect(FACE_CX - 8, MOUTH_Y, 16, 3, C_MOUTH);
}

static void drawWorkingV1(Adafruit_ST7789& tft, WorkSubtype ws) {  // Progress bar
    drawEyePair(tft, C_EYE, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W, EYE_H - 6, false);
    // Race goggles
    tft.drawRoundRect(L_EYE_X - EYE_W/2 - 1, EYE_Y - EYE_H/2 - 1,
        EYE_W + 2, EYE_H - 4, 3, C_SPARKLE);
    tft.drawRoundRect(R_EYE_X - EYE_W/2 - 1, EYE_Y - EYE_H/2 - 1,
        EYE_W + 2, EYE_H - 4, 3, C_SPARKLE);
    // Progress bar
    int bw = 100, bh = 4, bx = FACE_CX - bw/2, by = MOUTH_Y + 6;
    tft.fillRoundRect(bx, by, bw, bh, 2, 0x4228);
    int fill = (millis() / 20) % bw;
    tft.fillRoundRect(bx, by, fill, bh, 2, C_EYE);
}

static void drawWorkingV2(Adafruit_ST7789& tft, WorkSubtype ws) {  // Radar / scanning
    drawEyePair(tft, C_EYE, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W, EYE_H - 10, false);
    // Radar sweep arc
    float sweep = (millis() * 0.004f);
    int rr = 18;
    int rx = FACE_CX, ry = EYE_Y - 30;
    for (int i = 0; i < 7; i++) {
        float a = sweep - i * 0.3f;
        int16_t ex = rx + cos(a) * rr;
        int16_t ey = ry + sin(a) * rr;
        tft.drawPixel(ex, ey, C_EYE);
    }
    _circle(tft, rx, ry, rr, C_EYE);
    _circle(tft, rx, ry, rr/2, C_EYE);
    tft.fillRect(FACE_CX - 8, MOUTH_Y, 16, 3, C_MOUTH);
}

// ==================== COMPLETED STATE (3 variants) ====================

static void drawCompletedV0(Adafruit_ST7789& tft) {  // Star eyes
    for (int s = -1; s <= 1; s+=2) {
        int16_t cx = (s == -1) ? L_EYE_X : R_EYE_X;
        int16_t cy = EYE_Y - 4;
        for (int j = 0; j < 4; j++) {
            float a = j * 3.14159f / 2;
            tft.drawLine(
                cx + 14*cos(a), cy - 14*sin(a),
                cx + 5*cos(a+0.785f), cy - 5*sin(a+0.785f), C_DONE);
            tft.drawLine(
                cx + 14*cos(a), cy - 14*sin(a),
                cx + 5*cos(a-0.785f), cy - 5*sin(a-0.785f), C_DONE);
        }
        _circle(tft, cx, cy, 4, C_DONE);
    }
    // Big smile
    for (int i = 0; i < 10; i++) {
        int16_t xo = 22 * i / 10;
        tft.drawFastHLine(FACE_CX - 18, MOUTH_Y - 4 + i, xo*2, C_DONE);
        tft.drawFastHLine(FACE_CX - 18, MOUTH_Y - 4 + i, xo*2, C_DONE);
        // Actually a curved smile
        tft.drawFastHLine(FACE_CX - xo, MOUTH_Y + i, xo*2, C_DONE);
    }
}

static void drawCompletedV1(Adafruit_ST7789& tft) {  // Squint + blush happy
    for (int s = -1; s <= 1; s+=2) {
        int16_t cx = (s == -1) ? L_EYE_X : R_EYE_X;
        tft.fillRect(cx - 16, EYE_Y - 3, 32, 6, C_EYE);
    }
    // Big smile
    tft.fillRect(FACE_CX - 18, MOUTH_Y, 36, 3, C_DONE);
    for (int i = 0; i < 10; i++) {
        int16_t xo = 18 * i / 10;
        tft.drawFastHLine(FACE_CX - 18, MOUTH_Y + 1 + i, xo, C_DONE);
        tft.drawFastHLine(FACE_CX + 18 - xo, MOUTH_Y + 1 + i, xo, C_DONE);
    }
    _circle(tft, L_EYE_X - 18, EYE_Y + 10, 6, C_BLUSH);
    _circle(tft, R_EYE_X + 18, EYE_Y + 10, 6, C_BLUSH);
}

static void drawCompletedV2(Adafruit_ST7789& tft) {  // Jump bounce animation
    float bounce = sin(millis() * 0.015f) * 5;
    int16_t bx = bounce * 0.3f;
    int16_t by = bounce;

    // Round eyes
    _circle(tft, L_EYE_X, EYE_Y + by, 14, C_EYE);
    _circle(tft, R_EYE_X, EYE_Y + by, 14, C_EYE);
    // Sparkle in eyes
    _circle(tft, L_EYE_X - 5, EYE_Y + by - 6, 3, C_SPARKLE);
    _circle(tft, R_EYE_X - 5, EYE_Y + by - 6, 3, C_SPARKLE);
    // Wide smile
    tft.fillRoundRect(FACE_CX - 16, MOUTH_Y + by - 4, 32, 12, 4, C_DONE);
    tft.fillRoundRect(FACE_CX - 14, MOUTH_Y + by - 3, 28, 8, 3, C_BG);
}

// ==================== SLEEP STATE (2 variants) ====================

static void drawSleepV0(Adafruit_ST7789& tft) {
    drawEyePair(tft, C_SLEEP, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W, 4, true);
    // ZZZ
    int ph = (millis() / 200) % 24;
    tft.setTextColor(C_SLEEP);
    if (ph > 3)  { tft.setTextSize(1); tft.setCursor(R_EYE_X + 14, EYE_Y - 16 - ph/2); tft.print("z"); }
    if (ph > 9)  { tft.setTextSize(2); tft.setCursor(R_EYE_X + 20, EYE_Y - 30 - ph/2); tft.print("Z"); }
    if (ph > 16) { tft.setTextSize(3); tft.setCursor(R_EYE_X + 28, EYE_Y - 50 - ph/2); tft.print("Z"); }
}

static void drawSleepV1(Adafruit_ST7789& tft) {
    drawEyePair(tft, C_SLEEP, L_EYE_X, EYE_Y, R_EYE_X, EYE_Y,
        EYE_W, 4, true);
    // Sleep bubble
    float breathe = 0.5f + 0.5f * sin(millis() * 0.002f);
    int bx = R_EYE_X + 14;
    int by = EYE_Y - 30 - (millis() / 200 % 20);
    _circle(tft, bx, by, 8, C_SLEEP);
    _circle(tft, bx + 2, by - 2, 2, C_BG);
}

// ==================== ERROR STATE (2 variants) ====================

static void drawErrorV0(Adafruit_ST7789& tft) {
    for (int s = -1; s <= 1; s+=2) {
        int16_t cx = (s == -1) ? L_EYE_X : R_EYE_X;
        tft.drawLine(cx - 12, EYE_Y - 12, cx + 12, EYE_Y + 12, C_ERROR);
        tft.drawLine(cx + 12, EYE_Y - 12, cx - 12, EYE_Y + 12, C_ERROR);
    }
    // Frown
    for (int i = 0; i < 7; i++) {
        int16_t xo = 18 * i / 7;
        tft.drawFastHLine(FACE_CX - 16, MOUTH_Y - 2 - i, xo, C_ERROR);
        tft.drawFastHLine(FACE_CX + 16 - xo, MOUTH_Y - 2 - i, xo, C_ERROR);
    }
}

static void drawErrorV1(Adafruit_ST7789& tft) {
    drawErrorV0(tft);
    // Flashing error text
    if ((millis() / 500) % 2) {
        tft.setTextSize(1);
        tft.setTextColor(C_ERROR);
        tft.setCursor(FACE_CX - 12, MOUTH_Y + 16);
        tft.print("ERR");
    }
}

// ==================== DISCONNECTED STATE ====================

static void drawDisconnected(Adafruit_ST7789& tft) {
    // Static/snow effect
    for (int i = 0; i < 20; i++) {
        int16_t px = random(40, 200);
        int16_t py = random(20, 180);
        tft.drawPixel(px, py, C_SPARKLE);
    }
    // Big X eyes
    for (int s = -1; s <= 1; s+=2) {
        int16_t cx = (s == -1) ? L_EYE_X : R_EYE_X;
        tft.drawLine(cx - 16, EYE_Y - 16, cx + 16, EYE_Y + 16, C_SLEEP);
        tft.drawLine(cx + 16, EYE_Y - 16, cx - 16, EYE_Y + 16, C_SLEEP);
    }
    tft.setTextSize(1);
    tft.setTextColor(C_SLEEP);
    tft.setCursor(FACE_CX - 42, MOUTH_Y + 10);
    tft.print("NO SIGNAL");
}

// ==================== MAIN DRAW DISPATCH ====================

static void drawStateExpression(Adafruit_ST7789& tft) {
    tft.fillScreen(C_BG);

    // Clear text area for face region
    tft.fillRect(30, 20, 180, 170, C_BG);

    switch (st.state) {
        case ST_IDLE: {
            bool blink = false;
            if ((millis() % 3000) < 150) blink = true;  // 150ms blink every 3s
            switch (st.expr_variant) {
                case 0: drawIdleV0(tft, blink); break;
                case 1: drawIdleV1(tft, blink); break;
                case 2: drawIdleV2(tft, blink); break;
            }
            break;
        }
        case ST_THINKING: {
            switch (st.expr_variant) {
                case 0: drawThinkingV0(tft); break;
                case 1: drawThinkingV1(tft); break;
                case 2: drawThinkingV2(tft); break;
            }
            break;
        }
        case ST_WORKING: {
            switch (st.expr_variant) {
                case 0: drawWorkingV0(tft, st.work_subtype); break;
                case 1: drawWorkingV1(tft, st.work_subtype); break;
                case 2: drawWorkingV2(tft, st.work_subtype); break;
            }
            break;
        }
        case ST_COMPLETED: {
            switch (st.expr_variant) {
                case 0: drawCompletedV0(tft); break;
                case 1: drawCompletedV1(tft); break;
                case 2: drawCompletedV2(tft); break;
            }
            // Spawn particles on state entry
            static bool particles_spawned = false;
            if (!particles_spawned) {
                spawnParticles(15, FACE_CX, EYE_Y);
                particles_spawned = true;
            }
            updateParticles(tft);
            break;
        }
        case ST_SLEEP: {
            switch (st.expr_variant) {
                case 0: drawSleepV0(tft); break;
                case 1: drawSleepV1(tft); break;
                case 2: drawSleepV0(tft); break;
            }
            break;
        }
        case ST_ERROR: {
            switch (st.expr_variant) {
                case 0: drawErrorV0(tft); break;
                case 1: drawErrorV1(tft); break;
                case 2: drawErrorV0(tft); break;
            }
            break;
        }
        case ST_DISCONNECTED: {
            drawDisconnected(tft);
            break;
        }
        default: break;
    }

    // Reset particles when leaving completed state
    if (st.state != ST_COMPLETED) particle_count = 0;
}

#endif
