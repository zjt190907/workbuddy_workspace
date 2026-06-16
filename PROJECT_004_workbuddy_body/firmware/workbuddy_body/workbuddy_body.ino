// ============================================================
// WorkBuddy Body — Main Firmware
// ============================================================
// ESP32-C3 SuperMini + ST7789 1.54" 240x240 TFT LCD
//
// Features:
//   - Animated facial expressions (idle, happy, thinking, etc.)
//   - WiFi AP mode web controller (no app needed)
//   - Canvas drawing mode (draw on screen from phone)
//   - Configurable animation speed & colors
//   - Display on/off (backlight control)
//
// Arduino IDE Settings:
//   Board: "ESP32C3 Dev Module"
//   USB CDC On Boot: "Enabled"
//   CPU Frequency: 160 MHz
//   Upload Speed: 921600
//
// Required Libraries:
//   - Adafruit GFX Library
//   - Adafruit ST7735 and ST7789 Library
// ============================================================

#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <WiFi.h>
#include <WebServer.h>

#include "expressions.h"
#include "web_pages.h"

// ==================== PIN DEFINITIONS ====================
// ESP32-C3 SuperMini → ST7789 1.54" TFT 240x240
//
// CRITICAL NOTES:
//   - Connect VCC to 3V3 only — NEVER 5V!
//   - GPIO 6/7 are connected to internal flash — do NOT use for SPI.
//   - GPIO 8 is a strapping pin: LOW at reset = Download Boot mode!
//     ST7789 SCK idles LOW, so GPIO 8 would prevent normal boot.
//     FIX: Use GPIO 5 for SCK instead of GPIO 8.

#define TFT_SCK    5    // GPIO 5  → SCL (SPI Clock) — was GPIO 8
#define TFT_MOSI   10   // GPIO 10 → SDA (SPI MOSI)
#define TFT_RST    2    // GPIO 2  → RES (Reset)
#define TFT_DC     1    // GPIO 1  → DC  (Data/Command)
#define TFT_CS     4    // GPIO 4  → CS  (Chip Select)
#define TFT_BL     3    // GPIO 3  → BL  (Backlight)

// ==================== WIFI AP CONFIG ====================

#define AP_SSID    "WorkBuddy-Body"
#define AP_PASS    "buddy1234"
#define AP_CHANNEL 1
#define AP_MAX_CONN 4

// ==================== GLOBALS ====================

// Use software SPI (5-param constructor) since SCK=GPIO5 is not a default FSPI pin
Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCK, TFT_RST);
WebServer server(80);

AnimState anim = {
    .current        = EXPR_LOGO,
    .last_blink_ms  = 0,
    .blinking       = false,
    .blink_duration = 150,
    .blink_interval = 3500,
    .anim_frame     = 0,
    .anim_timer     = 0,
    .bg_color       = COL_BG,
    .eye_color      = COL_EYE,
    .pen_color      = COL_EYE,
    .speed          = 2,       // Normal
    .display_on     = true,
};

// ==================== COLOR CONVERSION ====================
// Web color picker sends 24-bit RGB888 (e.g. #ff0000 = red)
// ST7789 display needs 16-bit RGB565 (5R 6G 5B)
// Must convert, otherwise colors are completely wrong!

inline uint16_t rgb888_to_rgb565(uint32_t rgb888) {
    uint8_t r = (rgb888 >> 16) & 0xFF;
    uint8_t g = (rgb888 >> 8)  & 0xFF;
    uint8_t b =  rgb888        & 0xFF;
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
}

// ==================== WIFI & WEB SERVER ====================

void initWiFi() {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASS, AP_CHANNEL, false, AP_MAX_CONN);
    Serial.println("[WiFi] AP started: " AP_SSID);
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.softAPIP());
}

void handleRoot() {
    server.send_P(200, "text/html", PAGE_INDEX);
}

void handleExpr() {
    String name = server.arg("name");
    if (name.length() == 0 && server.hasArg("name") == false) {
        String uri = server.uri();
        if (uri.startsWith("/api/expr/")) {
            name = uri.substring(10);
        }
    }
    if (name.length() > 0) {
        Expression e = getExpressionByName(name);
        anim.current = e;
        anim.anim_frame = 0;
        Serial.println("[Expr] Set: " + String(getExpressionName(e)));
    }
    server.send(200, "text/plain", "OK");
}

void handleSpeed() {
    int speed = 2;
    String val = server.arg("value");
    if (val.length() > 0) {
        speed = constrain(val.toInt(), 1, 3);
    } else {
        String uri = server.uri();
        if (uri.startsWith("/api/speed/")) {
            speed = constrain(uri.substring(11).toInt(), 1, 3);
        }
    }
    anim.speed = speed;
    server.send(200, "text/plain", "speed=" + String(anim.speed));
}

void handleBg() {
    String val = server.arg("color");
    if (val.length() == 0) {
        String uri = server.uri();
        if (uri.startsWith("/api/bg/")) {
            val = uri.substring(8);
        }
    }
    if (val.length() >= 6) {
        uint32_t rgb888 = (uint32_t)strtol(val.c_str(), NULL, 16);
        anim.bg_color = rgb888_to_rgb565(rgb888);
    }
    server.send(200, "text/plain", "bg=0x" + String(anim.bg_color, HEX));
}

void handlePen() {
    String val = server.arg("color");
    if (val.length() == 0) {
        String uri = server.uri();
        if (uri.startsWith("/api/pen/")) {
            val = uri.substring(9);
        }
    }
    if (val.length() >= 6) {
        uint32_t rgb888 = (uint32_t)strtol(val.c_str(), NULL, 16);
        anim.pen_color = rgb888_to_rgb565(rgb888);
        // Also update eye_color so expressions use the new color
        anim.eye_color = anim.pen_color;
    }
    server.send(200, "text/plain", "pen=0x" + String(anim.pen_color, HEX));
}

void handleDisplay() {
    String val = server.arg("state");
    if (val.length() == 0) {
        String uri = server.uri();
        if (uri.startsWith("/api/display/")) {
            val = uri.substring(14);
        }
    }
    anim.display_on = (val == "1");
    if (anim.display_on) {
        digitalWrite(TFT_BL, HIGH);
    } else {
        digitalWrite(TFT_BL, LOW);
        clearScreen(tft, 0x0000);
    }
    server.send(200, "text/plain", anim.display_on ? "on" : "off");
}

void handlePixel() {
    if (anim.current != EXPR_CANVAS) {
        anim.current = EXPR_CANVAS;
    }
    int x = server.arg("x").toInt();
    int y = server.arg("y").toInt();
    String colorStr = server.arg("color");

    if (x == 0 && y == 0 && colorStr.length() == 0) {
        String uri = server.uri();
        if (uri.startsWith("/api/pixel/")) {
            String rest = uri.substring(11);
            int s1 = rest.indexOf('/');
            int s2 = rest.indexOf('/', s1 + 1);
            if (s1 > 0 && s2 > 0) {
                x = rest.substring(0, s1).toInt();
                y = rest.substring(s1 + 1, s2).toInt();
                colorStr = rest.substring(s2 + 1);
            }
        }
    }

    // Convert web RGB888 to ST7789 RGB565
    uint32_t rgb888 = (uint32_t)strtol(colorStr.c_str(), NULL, 16);
    uint16_t color = rgb888_to_rgb565(rgb888);

    // Draw a 3x3 pixel block for visibility
    tft.fillRect(x - 1, y - 1, 3, 3, color);
    server.send(200, "text/plain", "pixel");
}

void handleClear() {
    clearScreen(tft, anim.bg_color);
    server.send(200, "text/plain", "cleared");
}

void handleNotFound() {
    server.send(404, "text/plain", "Not Found");
}

void initWebServer() {
    server.on("/", handleRoot);

    // Query-param routes (reliable across all WebServer versions)
    server.on("/api/expr", HTTP_GET, handleExpr);
    server.on("/api/speed", HTTP_GET, handleSpeed);
    server.on("/api/bg", HTTP_GET, handleBg);
    server.on("/api/pen", HTTP_GET, handlePen);
    server.on("/api/display", HTTP_GET, handleDisplay);
    server.on("/api/pixel", HTTP_GET, handlePixel);
    server.on("/api/clear", HTTP_GET, handleClear);

    // Catch-all: parse path-based requests like /api/expr/happy
    server.onNotFound([]() {
        String uri = server.uri();
        if (uri.startsWith("/api/expr/"))       { handleExpr(); }
        else if (uri.startsWith("/api/speed/"))  { handleSpeed(); }
        else if (uri.startsWith("/api/bg/"))     { handleBg(); }
        else if (uri.startsWith("/api/pen/"))    { handlePen(); }
        else if (uri.startsWith("/api/display/")){ handleDisplay(); }
        else if (uri.startsWith("/api/pixel/"))  { handlePixel(); }
        else { server.send(404, "text/plain", "Not Found"); }
    });

    server.begin();
    Serial.println("[Web] Server started on port 80");
}

// ==================== DISPLAY INIT ====================

void initDisplay() {
    // Software SPI (5-param constructor) — no need to configure SPI bus
    // GPIO 5 for SCK avoids the strapping pin issue on GPIO 8
    tft.init(240, 240);
    tft.setRotation(0);  // Portrait, 0° rotation
    tft.fillScreen(COL_BG);

    // Set up backlight pin
    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);

    Serial.println("[Display] ST7789 240x240 initialized");
}

// ==================== SETUP ====================

void setup() {
    Serial.begin(115200);
    while (!Serial && millis() < 3000) {
        // Wait for serial, but timeout after 3s
    }
    Serial.println("\n========================================");
    Serial.println("  WorkBuddy Body v1.0");
    Serial.println("  ESP32-C3 + ST7789 240x240");
    Serial.println("========================================\n");

    // Init display first (show logo during WiFi setup)
    initDisplay();

    // Show boot logo
    anim.current = EXPR_LOGO;
    drawExpression(tft, anim, false);
    delay(1500);

    // Init WiFi AP
    initWiFi();

    // Init web server
    initWebServer();

    // Transition to idle expression
    anim.current = EXPR_IDLE;
    anim.anim_timer = millis();
    anim.last_blink_ms = millis();

    // Show WiFi info on screen briefly
    tft.fillScreen(COL_BG);
    tft.setTextSize(1);
    tft.setTextColor(COL_TEXT, COL_BG);
    tft.setCursor(20, 90);
    tft.print("WiFi: " AP_SSID);
    tft.setCursor(20, 108);
    tft.print("Pass: " AP_PASS);
    tft.setCursor(20, 126);
    tft.print("IP: ");
    tft.print(WiFi.softAPIP());
    tft.setCursor(20, 150);
    tft.setTextColor(COL_EYE, COL_BG);
    tft.print("http://");
    tft.print(WiFi.softAPIP());
    delay(3000);

    // Start idle expression
    drawExpression(tft, anim, false);

    Serial.println("[Setup] Complete — buddy is alive!");
}

// ==================== MAIN LOOP ====================

void loop() {
    // Handle web requests
    server.handleClient();

    // Update display animation
    uint32_t now = millis();
    updateAnimation(tft, anim, now);

    // Small delay to prevent CPU hogging
    // (web server still responsive within 20ms)
    delay(20);
}
