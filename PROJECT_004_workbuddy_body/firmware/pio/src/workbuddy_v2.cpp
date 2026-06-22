// ============================================================
// WorkBuddy Body V2 — Main Firmware
// ============================================================
// ESP32-C3 SuperMini + ST7789 1.54" 240x240 TFT
//
// Dual protocol: Serial JSON (primary, low-latency) + WiFi HTTP
// Rich expression engine with 3+ variants per state
// Particle effects, text overlays, smooth transitions
// ============================================================

#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <WiFi.h>
#include <WebServer.h>

#include "state_machine.h"
#include "serial_protocol.h"
#include "expressions_v2.h"
#include "text_overlay.h"

// ==================== PIN DEFINITIONS ====================

#define TFT_SCK    5
#define TFT_MOSI   10
#define TFT_RST    2
#define TFT_DC     1
#define TFT_CS     4
#define TFT_BL     3

// ==================== WIFI AP ====================

#define AP_SSID    "WorkBuddy-Body"
#define AP_PASS    "buddy1234"
#define AP_CHANNEL 1
#define AP_MAX_CONN 4

Adafruit_ST7789 tft = Adafruit_ST7789(TFT_CS, TFT_DC, TFT_MOSI, TFT_SCK, TFT_RST);
WebServer server(80);

// ==================== HTTP API (backward compatible) ====================

// Map web expression names to state machine
static void webSetState(const String& name) {
    if (name == "idle")      transitionTo(ST_IDLE);
    if (name == "happy")     transitionTo(ST_IDLE);  // happy = idle with smile
    if (name == "haha")      transitionTo(ST_IDLE);
    if (name == "thinking")  transitionTo(ST_THINKING);
    if (name == "working")   transitionTo(ST_WORKING);
    if (name == "done" || name == "completed") transitionTo(ST_COMPLETED);
    if (name == "sleeping" || name == "sleep")   transitionTo(ST_SLEEP);
    if (name == "error")     transitionTo(ST_ERROR);
    if (name == "boring")    transitionTo(ST_IDLE);
    if (name == "wake")      transitionTo(ST_IDLE);
    if (name == "canvas")    return;
}

void handleRoot() {
    String html = R"rawliteral(<!DOCTYPE html><html lang="zh"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WorkBuddy V2</title>
<style>
:root{--bg:#1a1a2e;--card:#16213e;--accent:#f5a623;--accent2:#e8850c;--text:#eee;--text2:#999;--border:#2a2a4a;--btn:#0f3460;--btn-h:#1a4a80;--r:10px;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:12px;}
h1{text-align:center;color:var(--accent);font-size:1.2em;padding:10px;}
.s{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:12px;margin:8px 0;}
.s h2{font-size:.8em;color:var(--accent);margin-bottom:8px;text-transform:uppercase;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;}
.btn{background:var(--btn);color:var(--text);border:1px solid var(--border);border-radius:var(--r);padding:12px 4px;font-size:.75em;cursor:pointer;text-align:center;transition:.15s;}
.btn:hover{background:var(--btn-h);}
.btn:active{transform:scale(.96);}
.btn.active{background:var(--accent2);color:#000;font-weight:bold;}
.btn .e{font-size:1.5em;display:block;}
.btn .l{font-size:.65em;color:var(--text2);margin-top:2px;}
.row{display:flex;justify-content:space-between;align-items:center;margin:6px 0;}
.row label{font-size:.75em;color:var(--text2);}
input[type=color]{width:36px;height:24px;border:1px solid var(--border);border-radius:4px;cursor:pointer;}
.st{text-align:center;font-size:.65em;color:var(--text2);padding:6px;}
</style></head><body>
<h1>WorkBuddy V2</h1>
<div class="s"><h2>State</h2><div class="grid3">
<div class="btn active" data-s="idle" onclick="set(this)"><span class="e">&#9678;</span><span class="l">Idle</span></div>
<div class="btn" data-s="thinking" onclick="set(this)"><span class="e">&#129300;</span><span class="l">Thinking</span></div>
<div class="btn" data-s="working" onclick="set(this,this.dataset.ss||'code')"><span class="e">&#9881;</span><span class="l">Working</span></div>
<div class="btn" data-s="completed" onclick="set(this)"><span class="e">&#11088;</span><span class="l">Done</span></div>
<div class="btn" data-s="sleep" onclick="set(this)"><span class="e">&#128564;</span><span class="l">Sleep</span></div>
<div class="btn" data-s="error" onclick="set(this)"><span class="e">&#9888;</span><span class="l">Error</span></div>
</div></div>
<div class="s"><h2>Work Subtype</h2><div class="grid2">
<div class="btn" data-ss="search" onclick="document.querySelector('[data-s=working]').dataset.ss='search';set(document.querySelector('[data-s=working]'))"><span class="e">&#128269;</span><span class="l">Search</span></div>
<div class="btn" data-ss="code" onclick="document.querySelector('[data-s=working]').dataset.ss='code';set(document.querySelector('[data-s=working]'))"><span class="e">&gt;_</span><span class="l">Code</span></div>
</div></div>
<div class="s"><h2>Text</h2>
<div style="display:flex;gap:6px;">
<input type="text" id="txt" placeholder="thinking text..." style="flex:1;background:var(--btn);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px;font-size:.8em;">
<button class="btn" onclick="sendtxt()" style="padding:8px 12px;">Send</button>
</div></div>
<div class="st" id="stat">v2.0</div>
<script>
function api(u){fetch('/api/'+u).then(r=>r.text()).then(t=>{document.getElementById('stat').textContent=t;}).catch(e=>{document.getElementById('stat').textContent='Error';});}
function set(el){document.querySelectorAll('[data-s]').forEach(b=>b.classList.remove('active'));el.classList.add('active');
var s=el.dataset.s;if(s==='sleep'||s==='completed'){api(s);}else{var ss=el.dataset.ss||'';api('state?value='+s+(ss?'&subtype='+ss:''));}}
function sendtxt(){var t=document.getElementById('txt').value;if(t)api('text?value='+encodeURIComponent(t));}
</script></body></html>)rawliteral";
    server.send(200, "text/html", html);
}

void handleState() {
    if (server.hasArg("value")) {
        String val = server.arg("value");
        if (val == "working" && server.hasArg("subtype")) {
            String stype = server.arg("subtype");
            if (stype == "search") st.work_subtype = WS_SEARCH;
            else if (stype == "code") st.work_subtype = WS_CODE;
            else if (stype == "file") st.work_subtype = WS_FILE;
            else if (stype == "api") st.work_subtype = WS_API;
        }
        webSetState(val);
        st.last_wifi_ms = millis();
        st.ever_connected = true;
    }
    server.send(200, "text/plain", stateName(st.state));
}

void handleText() {
    if (server.hasArg("value")) {
        String val = server.arg("value");
        strncpy(st.text_buf, val.c_str(), sizeof(st.text_buf) - 1);
        st.text_dirty = true;
        st.last_wifi_ms = millis();
        st.ever_connected = true;
    }
    server.send(200, "text/plain", "ok");
}

void handleSleep() { st.last_wifi_ms = millis(); st.ever_connected = true; transitionTo(ST_SLEEP); server.send(200, "text/plain", "sleep"); }
void handleWake()   { st.last_wifi_ms = millis(); st.ever_connected = true; transitionTo(ST_IDLE); server.send(200, "text/plain", "idle"); }

void initWebServer() {
    server.on("/", handleRoot);
    server.on("/api/state", HTTP_GET, handleState);
    server.on("/api/expr", HTTP_GET, handleState);  // backward compat
    server.on("/api/text", HTTP_GET, handleText);
    server.on("/api/sleep", HTTP_GET, handleSleep);
    server.on("/api/wake", HTTP_GET, handleWake);
    server.on("/api/completed", HTTP_GET, handleSleep);  // trigger completed

    server.onNotFound([]() {
        String uri = server.uri();
        if (uri.startsWith("/api/sleep")) { handleSleep(); }
        else if (uri.startsWith("/api/wake")) { handleWake(); }
        else { server.send(404, "text/plain", "v2: use /api/state?value=xxx"); }
    });
    server.begin();
}

// ==================== DISPLAY SETUP ====================

void initDisplay() {
    tft.init(240, 240);
    tft.setRotation(0);
    tft.fillScreen(C_BG);

    pinMode(TFT_BL, OUTPUT);
    digitalWrite(TFT_BL, HIGH);
}

void showBootLogo() {
    tft.fillScreen(C_BG);
    tft.setTextSize(2);
    tft.setTextColor(C_EYE);
    tft.setCursor(FACE_CX - 10, FACE_CY - 16);
    tft.print("W");
    tft.setTextSize(1);
    tft.setTextColor(0xFFFF);
    tft.setCursor(FACE_CX - 30, FACE_CY + 8);
    tft.print("WorkBuddy");
    tft.setCursor(FACE_CX - 10, FACE_CY + 22);
    tft.print("V2");
    delay(1500);
}

// ==================== IDLE PHRASES ====================

static const char* idle_phrases[] = {
    "我在哦～", "随时待命", "嗯？", "在线中", "等待指令", "zzz...",
};
#define IDLE_PHRASE_COUNT (sizeof(idle_phrases)/sizeof(char*))

// ==================== SETUP ====================

void setup() {
    Serial.begin(115200);
    delay(1500);  // USB CDC enum

    Serial.println("\nWorkBuddy Body V2");
    Serial.println("Dual-mode: Serial JSON + WiFi HTTP");

    randomSeed(analogRead(0) + millis());

    initDisplay();
    showBootLogo();

    // Init WiFi
    WiFi.mode(WIFI_AP);
    WiFi.softAP(AP_SSID, AP_PASS, AP_CHANNEL, false, AP_MAX_CONN);
    Serial.print("[WiFi] " AP_SSID " @ ");
    Serial.println(WiFi.softAPIP());

    initWebServer();

    // Start in idle
    transitionTo(ST_IDLE);
    Serial.println("[Ready] Accepting commands on Serial + WiFi");
}

// ==================== MAIN LOOP ====================

void loop() {
    server.handleClient();      // Handle HTTP requests
    serialPoll();                // Handle Serial JSON commands

    uint32_t now = millis();

    // === Disconnect detection (DISABLED — causing false positives) ===
    // TODO: re-enable when serial protocol is stable

    // === Idle → auto-sleep ===
    if (st.state == ST_IDLE && st.idle_start_ms > 0 &&
        now - st.idle_start_ms > IDLE_SLEEP_TIMEOUT_MS) {
        transitionTo(ST_SLEEP);
    }

    // === Completed → auto-idle ===
    if (st.state == ST_COMPLETED &&
        now - st.state_start_ms > COMPLETED_DISPLAY_MS) {
        transitionTo(ST_IDLE);
    }

    // === Transition animation ===
    if (st.transitioning) {
        if (now - st.trans_start_ms > 400) {
            st.transitioning = false;
        }
    }

    // === Draw expression (at ~15fps) ===
    static uint32_t last_draw = 0;
    if (now - last_draw >= 66) {  // ~15fps
        drawStateExpression(tft);
        last_draw = now;
    }

    // === Text overlay ===
    if (st.text_dirty) {
        updateTextContent(st.text_buf);
        st.text_dirty = false;
    }

    // Draw text when active, or in thinking/working/completed states
    if (txt.active || st.state == ST_THINKING || st.state == ST_WORKING || st.state == ST_COMPLETED) {
        drawTextOverlay(tft);
    }

    // Idle phrases (only when no manual text is active)
    if (st.state == ST_IDLE && !txt.active) {
        static uint32_t last_idle_phrase = 0;
        if (now - last_idle_phrase > 8000) {
            last_idle_phrase = now;
            updateTextContent(idle_phrases[st.idle_phrase_idx % IDLE_PHRASE_COUNT]);
            st.idle_phrase_idx++;
            drawTextOverlay(tft);
            delay(2000);
            clearTextArea(tft);
            txt.active = false;
        }
    }

    // === Backlight breathing (sleep state) ===
    if (st.state == ST_SLEEP) {
        float b = 0.3f + 0.35f * (1 + sin(now * 0.003f));
        analogWrite(TFT_BL, (int)(b * 255));
    } else {
        analogWrite(TFT_BL, 255);
    }

    delay(8);
}
