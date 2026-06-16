// ============================================================
// WorkBuddy Body — Expression Drawing Functions V2
// ============================================================
// 10 diverse expressions for "一" (Yi) the AI companion.
// Display: ST7789 240x240 | Coordinate: (0,0) top-left
// ============================================================

#ifndef EXPRESSIONS_H
#define EXPRESSIONS_H

#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>

// ==================== LAYOUT ====================

#define SCR_W           240
#define SCR_H           240

// Eye positioning
#define EYE_W           28
#define EYE_H           50
#define EYE_GAP         56
#define EYE_CY          (SCR_H/2 - 10)

#define L_EYE_CX        (SCR_W/2 - EYE_GAP/2 - EYE_W/2)
#define R_EYE_CX        (SCR_W/2 + EYE_GAP/2 + EYE_W/2)

// Mouth area
#define MOUTH_CX        (SCR_W/2)
#define MOUTH_CY        (SCR_H/2 + 50)

// Colors
#define COL_BG          0x2104
#define COL_EYE         0xFBE0
#define COL_MOUTH       0xFBE0
#define COL_TEXT        0xFFFF
#define COL_ERR         0xF800
#define COL_SLEEP       0x7BEF
#define COL_PROGRESS    0x05F0
#define COL_BLUSH       0xF9A6  // pinkish for blush

// ==================== ENUM ====================

enum Expression {
    EXPR_IDLE = 0,
    EXPR_HAPPY,
    EXPR_HAHA,
    EXPR_THINKING,
    EXPR_WORKING,
    EXPR_DONE,
    EXPR_SLEEPING,
    EXPR_ERROR,
    EXPR_BORING,
    EXPR_LOGO,
    EXPR_CANVAS,
    EXPR_COUNT
};

struct AnimState {
    Expression current;
    uint32_t    last_blink_ms;
    bool        blinking;
    uint32_t    blink_duration;
    uint32_t    blink_interval;
    uint8_t     anim_frame;
    uint32_t    anim_timer;
    uint16_t    bg_color;
    uint16_t    eye_color;
    uint16_t    pen_color;
    int8_t      speed;
    bool        display_on;
};

// ==================== HELPERS ====================

inline void drawRoundedRect(Adafruit_ST7789 &tft,
    int16_t x, int16_t y, int16_t w, int16_t h, int16_t r, uint16_t c) {
    tft.fillRoundRect(x - w/2, y - h/2, w, h, r, c);
}

inline void clearScreen(Adafruit_ST7789 &tft, uint16_t bg) {
    tft.fillScreen(bg);
}

// Draw a circle centered at (cx, cy)
inline void drawCircle(Adafruit_ST7789 &tft, int16_t cx, int16_t cy,
    int16_t r, uint16_t c) {
    tft.fillCircle(cx, cy, r, c);
}

// Draw an upward arc smile centered at (cx, base_y)
static void drawSmile(Adafruit_ST7789 &tft, int16_t cx, int16_t base_y,
    int16_t w, int16_t h, uint16_t c) {
    tft.fillRect(cx - w/2, base_y, w, 3, c);
    for (int i = 0; i < h; i++) {
        int16_t xo = (int16_t)((float)i / h * (w/2));
        tft.drawFastHLine(cx - w/2, base_y + i, xo, c);
        tft.drawFastHLine(cx + w/2 - xo, base_y + i, xo, c);
    }
}

// Draw a downward arc frown
static void drawFrown(Adafruit_ST7789 &tft, int16_t cx, int16_t base_y,
    int16_t w, int16_t h, uint16_t c) {
    tft.fillRect(cx - w/2, base_y, w, 2, c);
    for (int i = 0; i < h; i++) {
        int16_t xo = (int16_t)((float)i / h * (w/2));
        tft.drawFastHLine(cx - w/2, base_y - i, xo, c);
        tft.drawFastHLine(cx + w/2 - xo, base_y - i, xo, c);
    }
}

// ==================== EXPRESSIONS ====================

// --- IDLE: Round eyes with blink ---
static void drawIdle(Adafruit_ST7789 &tft, AnimState &st, bool blink) {
    clearScreen(tft, st.bg_color);
    if (blink) {
        tft.fillRect(L_EYE_CX - EYE_W/2, EYE_CY - 2, EYE_W, 4, st.eye_color);
        tft.fillRect(R_EYE_CX - EYE_W/2, EYE_CY - 2, EYE_W, 4, st.eye_color);
    } else {
        drawRoundedRect(tft, L_EYE_CX, EYE_CY, EYE_W, EYE_H, 5, st.eye_color);
        drawRoundedRect(tft, R_EYE_CX, EYE_CY, EYE_W, EYE_H, 5, st.eye_color);
    }
    tft.fillRect(MOUTH_CX - 12, MOUTH_CY, 24, 3, COL_MOUTH);
}

// --- HAPPY: Simple cute smiley — round eyes, gentle smile, blush dots ---
static void drawHappy(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    // Big round eyes
    int16_t eye_r = 16;
    drawCircle(tft, L_EYE_CX, EYE_CY - 2, eye_r, st.eye_color);
    drawCircle(tft, R_EYE_CX, EYE_CY - 2, eye_r, st.eye_color);

    // Eye sparkle highlights (small white dots)
    drawCircle(tft, L_EYE_CX - 4, EYE_CY - 8, 3, 0xFFFF);
    drawCircle(tft, R_EYE_CX - 4, EYE_CY - 8, 3, 0xFFFF);

    // Blush marks (small circles below/outside eyes)
    drawCircle(tft, L_EYE_CX - 18, EYE_CY + 8, 6, COL_BLUSH);
    drawCircle(tft, R_EYE_CX + 18, EYE_CY + 8, 6, COL_BLUSH);

    // Gentle smile
    drawSmile(tft, MOUTH_CX, MOUTH_CY, 30, 10, COL_MOUTH);
}

// --- HAHA: Laughing — anime-style ^-^ eyes, wide open mouth ---
static void drawHaha(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    int16_t eye_w = 32, arc_h = 10;

    // Left eye: ^ arc (laughing squint)
    tft.fillRect(L_EYE_CX - eye_w/2, EYE_CY, eye_w, 3, st.eye_color);
    for (int i = 1; i <= arc_h; i++) {
        int16_t xo = eye_w/2 * i / arc_h;
        tft.drawFastHLine(L_EYE_CX - eye_w/2, EYE_CY - i, xo, st.eye_color);
        tft.drawFastHLine(L_EYE_CX + eye_w/2 - xo, EYE_CY - i, xo, st.eye_color);
    }

    // Right eye: ^ arc
    tft.fillRect(R_EYE_CX - eye_w/2, EYE_CY, eye_w, 3, st.eye_color);
    for (int i = 1; i <= arc_h; i++) {
        int16_t xo = eye_w/2 * i / arc_h;
        tft.drawFastHLine(R_EYE_CX - eye_w/2, EYE_CY - i, xo, st.eye_color);
        tft.drawFastHLine(R_EYE_CX + eye_w/2 - xo, EYE_CY - i, xo, st.eye_color);
    }

    // Tears of joy (tiny dots near eyes)
    drawCircle(tft, L_EYE_CX - 16, EYE_CY + 4, 3, st.eye_color);
    drawCircle(tft, R_EYE_CX + 16, EYE_CY + 4, 3, st.eye_color);

    // Wide open laughing mouth (dark oval)
    tft.fillRoundRect(MOUTH_CX - 14, MOUTH_CY - 4, 28, 18, 6, 0x0000);
    tft.fillRoundRect(MOUTH_CX - 14, MOUTH_CY - 4, 28, 18, 6, COL_MOUTH);
    tft.fillRoundRect(MOUTH_CX - 12, MOUTH_CY - 4, 24, 16, 4, 0x0000);
}

// --- THINKING: One eye open, one squinted, ... dots ---
static void drawThinking(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    // Left eye: normal
    drawRoundedRect(tft, L_EYE_CX, EYE_CY, EYE_W - 2, EYE_H - 6, 5, st.eye_color);

    // Right eye: squinted thin line
    tft.fillRect(R_EYE_CX - EYE_W/2, EYE_CY - 2, EYE_W, 5, st.eye_color);

    // Animated thinking dots
    int dc = (st.anim_frame % 3) + 1;
    tft.setTextSize(2);
    tft.setTextColor(st.eye_color, st.bg_color);
    tft.setCursor(MOUTH_CX - 12, MOUTH_CY - 5);
    for (int i = 0; i < dc; i++) tft.print(".");
}

// --- WORKING: Eyes + progress bar ---
static void drawWorking(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    drawRoundedRect(tft, L_EYE_CX, EYE_CY, EYE_W, EYE_H, 5, st.eye_color);
    drawRoundedRect(tft, R_EYE_CX, EYE_CY, EYE_W, EYE_H, 5, st.eye_color);

    tft.fillRoundRect(MOUTH_CX - 7, MOUTH_CY - 3, 14, 8, 3, COL_MOUTH);

    int16_t bw = 160, bh = 6, bx = (SCR_W - bw)/2, by = SCR_H - 30;
    tft.fillRoundRect(bx, by, bw, bh, 3, 0x4208);
    int16_t fw = (int16_t)((st.anim_frame % 100) / 100.0 * bw);
    if (fw > 2) tft.fillRoundRect(bx, by, fw, bh, 3, COL_PROGRESS);
}

// --- DONE: Star eyes + big smile — celebration! ---
static void drawDone(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    // Star eyes: draw a ☆ shape at each eye center
    uint16_t ec = st.eye_color;
    int16_t r = 14, r2 = 6;
    for (int s = -1; s <= 1; s += 2) {
        int16_t cx = (s == -1) ? L_EYE_CX : R_EYE_CX;
        int16_t cy = EYE_CY - 2;
        // 4-point star
        for (int j = 0; j < 4; j++) {
            float a = j * 3.14159 / 2;
            tft.drawLine(
                cx + r * cos(a), cy - r * sin(a),
                cx + r2 * cos(a + 0.785), cy - r2 * sin(a + 0.785), ec);
            tft.drawLine(
                cx + r * cos(a), cy - r * sin(a),
                cx + r2 * cos(a - 0.785), cy - r2 * sin(a - 0.785), ec);
        }
        tft.fillCircle(cx, cy, 4, ec);
    }

    // Big happy smile
    drawSmile(tft, MOUTH_CX, MOUTH_CY, 36, 14, COL_MOUTH);

    // "DONE!" text
    tft.setTextSize(1);
    tft.setTextColor(COL_PROGRESS, st.bg_color);
    tft.setCursor(SCR_W/2 - 16, SCR_H - 22);
    tft.print("DONE!");
}

// --- SLEEPING: Closed eyes, ZZZ ---
static void drawSleeping(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    tft.fillRect(L_EYE_CX - EYE_W/2, EYE_CY - 2, EYE_W, 4, COL_SLEEP);
    tft.fillRect(R_EYE_CX - EYE_W/2, EYE_CY - 2, EYE_W, 4, COL_SLEEP);

    // ZZZ animation
    int ph = st.anim_frame % 30;
    int16_t zx = R_EYE_CX + 18, zy = EYE_CY - 24 - ph;
    tft.setTextColor(COL_SLEEP, st.bg_color);
    if (ph > 5) { tft.setTextSize(1); tft.setCursor(zx, zy); tft.print("z"); }
    if (ph > 12) { tft.setTextSize(2); tft.setCursor(zx + 8, zy - 12); tft.print("Z"); }
    if (ph > 20) { tft.setTextSize(3); tft.setCursor(zx + 18, zy - 30); tft.print("Z"); }
}

// --- ERROR: X eyes, frown ---
static void drawError(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    int16_t xs = 14;
    for (int s = -1; s <= 1; s += 2) {
        int16_t cx = (s == -1) ? L_EYE_CX : R_EYE_CX;
        tft.drawLine(cx - xs, EYE_CY - xs, cx + xs, EYE_CY + xs, COL_ERR);
        tft.drawLine(cx + xs, EYE_CY - xs, cx - xs, EYE_CY + xs, COL_ERR);
    }

    drawFrown(tft, MOUTH_CX, MOUTH_CY, 32, 8, COL_ERR);

    tft.setTextColor(COL_ERR, st.bg_color);
    tft.setTextSize(1);
    tft.setCursor(SCR_W/2 - 16, SCR_H - 28);
    tft.print("ERROR");
}

// --- BORING: Half-lidded eyes looking sideways, flat/droopy mouth ---
static void drawBoring(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);

    // Half-covered eyes: draw lid over top half
    uint16_t lid = st.bg_color;
    for (int s = -1; s <= 1; s += 2) {
        int16_t cx = (s == -1) ? L_EYE_CX : R_EYE_CX;
        // Full eye outline
        drawRoundedRect(tft, cx, EYE_CY, EYE_W, EYE_H, 5, st.eye_color);
        // Lid covers top 60%
        tft.fillRect(cx - EYE_W/2 - 2, EYE_CY - EYE_H/2 - 1,
            EYE_W + 4, EYE_H * 3/5, lid);
        // Small pupil dot offset to one side
        drawCircle(tft, cx + 4, EYE_CY + 4, 5, st.eye_color);
    }

    // Flat/droopy mouth — just a straight short line
    tft.fillRect(MOUTH_CX - 10, MOUTH_CY + 2, 20, 2, COL_MOUTH);

    // Sigh text
    tft.setTextSize(1);
    tft.setTextColor(COL_SLEEP, st.bg_color);
    tft.setCursor(SCR_W/2 - 10, SCR_H - 24);
    tft.print("sigh");
}

// --- LOGO: Boot screen ---
static void drawLogo(Adafruit_ST7789 &tft, AnimState &st) {
    clearScreen(tft, st.bg_color);
    tft.setTextSize(5);
    tft.setTextColor(st.eye_color, st.bg_color);
    tft.setCursor(SCR_W/2 - 28, SCR_H/2 - 35);
    tft.print("W");
    tft.setTextSize(1);
    tft.setTextColor(COL_TEXT, st.bg_color);
    tft.setCursor(SCR_W/2 - 30, SCR_H/2 + 12);
    tft.print("WorkBuddy");
    tft.setCursor(SCR_W/2 - 14, SCR_H/2 + 26);
    tft.print("v2.0");
}

// --- CANVAS: Pixel drawing mode (no-op) ---
static void drawCanvas(Adafruit_ST7789 &tft, AnimState &st) {
    // Managed by web pixel commands
}

// ==================== DISPATCHER ====================

static void drawExpression(Adafruit_ST7789 &tft, AnimState &st, bool blink) {
    switch (st.current) {
        case EXPR_IDLE:     drawIdle(tft, st, blink);      break;
        case EXPR_HAPPY:    drawHappy(tft, st);             break;
        case EXPR_HAHA:     drawHaha(tft, st);              break;
        case EXPR_THINKING: drawThinking(tft, st);          break;
        case EXPR_WORKING:  drawWorking(tft, st);           break;
        case EXPR_DONE:     drawDone(tft, st);              break;
        case EXPR_SLEEPING: drawSleeping(tft, st);          break;
        case EXPR_ERROR:    drawError(tft, st);             break;
        case EXPR_BORING:   drawBoring(tft, st);            break;
        case EXPR_LOGO:     drawLogo(tft, st);              break;
        case EXPR_CANVAS:   drawCanvas(tft, st);            break;
        default:            drawIdle(tft, st, false);       break;
    }
}

// ==================== ANIMATION LOOP ====================

static uint32_t getAnimInterval(AnimState &st) {
    switch (st.speed) { case 1: return 200; case 3: return 50; default: return 100; }
}
static uint32_t getBlinkInterval(AnimState &st) {
    switch (st.speed) { case 1: return 5000; case 3: return 2000; default: return 3500; }
}

static void updateAnimation(Adafruit_ST7789 &tft, AnimState &st, uint32_t now) {
    if (!st.display_on) return;

    if (now - st.anim_timer >= getAnimInterval(st)) {
        st.anim_frame++; st.anim_timer = now;
    }

    bool blink = false;
    if (st.current == EXPR_IDLE) {
        if (!st.blinking && now - st.last_blink_ms >= st.blink_interval) {
            st.blinking = true; st.last_blink_ms = now;
        } else if (st.blinking && now - st.last_blink_ms >= 150) {
            st.blinking = false; st.blink_interval = getBlinkInterval(st);
            st.last_blink_ms = now;
        }
        blink = st.blinking;
    }

    drawExpression(tft, st, blink);
}

// ==================== NAME LOOKUP ====================

static const char* getExpressionName(Expression e) {
    switch (e) {
        case EXPR_IDLE:     return "idle";
        case EXPR_HAPPY:    return "happy";
        case EXPR_HAHA:     return "haha";
        case EXPR_THINKING: return "thinking";
        case EXPR_WORKING:  return "working";
        case EXPR_DONE:     return "done";
        case EXPR_SLEEPING: return "sleeping";
        case EXPR_ERROR:    return "error";
        case EXPR_BORING:   return "boring";
        case EXPR_LOGO:     return "logo";
        case EXPR_CANVAS:   return "canvas";
        default:            return "unknown";
    }
}

static Expression getExpressionByName(const String &name) {
    if (name == "idle")     return EXPR_IDLE;
    if (name == "happy")    return EXPR_HAPPY;
    if (name == "haha")     return EXPR_HAHA;
    if (name == "thinking") return EXPR_THINKING;
    if (name == "working")  return EXPR_WORKING;
    if (name == "done")     return EXPR_DONE;
    if (name == "sleeping") return EXPR_SLEEPING;
    if (name == "error")    return EXPR_ERROR;
    if (name == "boring")   return EXPR_BORING;
    if (name == "logo")     return EXPR_LOGO;
    if (name == "canvas")   return EXPR_CANVAS;
    return EXPR_IDLE;
}

#endif
