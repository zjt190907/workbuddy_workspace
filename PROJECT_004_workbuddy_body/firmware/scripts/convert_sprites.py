#!/usr/bin/env python3
"""
Sprite Converter — PNG → ST7789 RGB565 C Header
================================================
1. Reads all PNGs from image/ directory
2. Downscales to target_size (default 80x80)
3. Converts to ST7789 RGB565 (16-bit 5R/6G/5B)
4. Generates sprites.h with PROGMEM arrays
5. Generates sprites_render.cpp with drawing engine
"""

import os
import re
from collections import defaultdict
from PIL import Image

# ==================== CONFIG ====================
IMAGE_DIR = "D:/workBuddy_workspace/PROJECT_004_workbuddy_body/image"
OUTPUT_DIR = "D:/workBuddy_workspace/PROJECT_004_workbuddy_body/firmware/pio/src"
SPRITE_SIZE = (80, 80)  # width, height
DISPLAY_W = 240
DISPLAY_H = 240

# ==================== RGB888 → RGB565 ====================
def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def pil_to_rgb565(img):
    """Convert PIL RGBA/RGB image to bytearray of RGB565 pixels"""
    img = img.convert("RGBA")
    w, h = img.size
    data = bytearray(w * h * 2)
    pixels = img.load()
    idx = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a < 128:  # transparent → black
                r = g = b = 0
            val = rgb888_to_rgb565(r, g, b)
            data[idx] = (val >> 8) & 0xFF    # high byte first (big-endian for ST7789)
            data[idx + 1] = val & 0xFF
            idx += 2
    return bytes(data), w, h

# ==================== LOAD & PROCESS ====================
def discover_sprites():
    """Discover sprite files: name_frame.png"""
    pattern = re.compile(r'^([a-z]+)_(\d+)\.png$')
    sprites = defaultdict(list)
    for f in sorted(os.listdir(IMAGE_DIR)):
        m = pattern.match(f)
        if m:
            name, frame = m.group(1), int(m.group(2))
            sprites[name].append((frame, os.path.join(IMAGE_DIR, f)))
    for name in sprites:
        sprites[name].sort(key=lambda x: x[0])  # sort by frame number
    return sprites

# ==================== GENERATE C HEADER ====================
def c_byte_array(name, data):
    """Format byte data as C array"""
    lines = []
    lines.append(f"// {name}: {len(data)} bytes, {len(data)//2} pixels")
    lines.append(f"const PROGMEM uint8_t sprite_{name}[] = {{")
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hexes = ", ".join(f"0x{b:02X}" for b in chunk)
        lines.append(f"    {hexes},")
    lines.append("};")
    return "\n".join(lines)

def generate_header(sprites_data):
    """Generate sprites.h"""
    # Build sprite table
    sprite_list = sorted(sprites_data.keys())
    
    header = f"""// ============================================================
// WorkBuddy Body — Sprite Frames (Auto-Generated)
// ============================================================
// {len(sprite_list)} sprites, {SPRITE_SIZE[0]}x{SPRITE_SIZE[1]} pixels each
// Format: RGB565 big-endian, stored in PROGMEM
// ============================================================

#ifndef SPRITES_H
#define SPRITES_H

#include <Arduino.h>

// Sprite dimensions
#define SPRITE_W {SPRITE_SIZE[0]}
#define SPRITE_H {SPRITE_SIZE[1]}

// Sprite names
enum SpriteSet {{
    SPR_INVALID = -1,
"""
    for i, name in enumerate(sprite_list):
        header += f"    SPR_{name.upper()} = {i},\n"
    header += f"""    SPR_COUNT = {len(sprite_list)}
}};

// Sprite descriptor
struct Sprite {{
    const uint8_t* data;     // PROGMEM pointer
    uint16_t       num_frames;
}};

extern const Sprite sprite_sets[SPR_COUNT];
extern const char* getSpriteName(SpriteSet s);
extern SpriteSet getSpriteByName(const String& name);

"""
    # Raw pixel data arrays
    for name in sorted(sprites_data.keys()):
        frames = sprites_data[name]
        for fi, (pixels, w, h) in enumerate(frames):
            header += c_byte_array(f"{name}_{fi}", pixels) + "\n\n"
    
    header += "#endif // SPRITES_H\n"
    return header

def generate_impl(sprites_data):
    """Generate sprites_render.cpp"""
    sprite_list = sorted(sprites_data.keys())
    
    cpp = f"""// ============================================================
// WorkBuddy Body — Sprite Renderer (Auto-Generated)
// ============================================================
// Uses sprites.h data arrays to render sprite frames
// on ST7789 240x240 display.
// ============================================================

#include <Adafruit_ST7789.h>
#include "sprites.h"
#include "expressions.h"

// ==================== SPRITE TABLE ====================

const Sprite sprite_sets[SPR_COUNT] = {{
"""
    for name in sprite_list:
        num = len(sprites_data[name])
        cpp += f"    {{ sprite_{name}_0, {num} }},  // SPR_{name.upper()}\n"
    cpp += "};\n\n"

    # Name helpers
    cpp += """const char* getSpriteName(SpriteSet s) {
    switch (s) {
"""
    for name in sprite_list:
        cpp += f'        case SPR_{name.upper()}: return "{name}";\n'
    cpp += """        default: return "unknown";
    }
}

SpriteSet getSpriteByName(const String& name) {
"""
    for name in sprite_list:
        cpp += f'    if (name == "{name}") return SPR_{name.upper()};\n'
    cpp += """    return SPR_INVALID;
}

"""
    # Sprite draw helper
    cpp += f"""// ==================== SPRITE DRAW ====================

// Sprite frame tracking per expression
static uint8_t  sprite_frame_idx[EXPR_COUNT] = {{0}};
static uint32_t sprite_last_draw[EXPR_COUNT] = {{0}};

// Draw a sprite frame centered on screen
void drawSpriteFrame(Adafruit_ST7789& tft, SpriteSet s, uint8_t frame,
                     int16_t ox=0, int16_t oy=0, uint16_t bg=0x2104) {{
    if (s < 0 || s >= SPR_COUNT) return;
    if (frame >= sprite_sets[s].num_frames) frame = frame % sprite_sets[s].num_frames;

    int16_t sx = ({DISPLAY_W} - SPRITE_W) / 2 + ox;
    int16_t sy = ({DISPLAY_H} - SPRITE_H) / 2 + oy;

    // Draw frame from PROGMEM
    const uint8_t* data = sprite_sets[s].data + frame * SPRITE_W * SPRITE_H * 2;
    tft.drawRGBBitmap(sx, sy, data, SPRITE_W, SPRITE_H);
}}

// Map Expression → SpriteSet
SpriteSet exprToSprite(Expression ex) {{
    switch (ex) {{
"""
    mapping = {
        'idle': 'SPR_IDLE',
        'happy': 'SPR_HAPPY',
        'thinking': 'SPR_THINKING',
        'working': 'SPR_WORKING',
        'sleeping': 'SPR_SLEEPING',
        'error': 'SPR_ERROR',
    }
    for ename, spr in mapping.items():
        cpp += f"        case EXPR_{ename.upper()}: return {spr};\n"
    cpp += """        default: return SPR_IDLE;
    }
}

// Draw expression as sprite animation
void drawExpressionSprite(Adafruit_ST7789& tft, Expression ex, uint8_t speed=2) {
    SpriteSet s = exprToSprite(ex);
    if (s == SPR_INVALID) return;

    // Advance frame based on speed
    uint32_t now = millis();
    uint32_t interval = (4 - speed) * 150;  // speed 1=450ms, 2=300ms, 3=150ms
    if (now - sprite_last_draw[ex] >= interval) {
        sprite_frame_idx[ex]++;
        sprite_last_draw[ex] = now;
    }
    uint8_t frame = sprite_frame_idx[ex] % sprite_sets[s].num_frames;
    drawSpriteFrame(tft, s, frame);
}
"""
    return cpp

# ==================== MAIN ====================
def main():
    print("=== Sprite Converter ===")
    print(f"Image dir: {IMAGE_DIR}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Sprite size: {SPRITE_SIZE[0]}x{SPRITE_SIZE[1]}")
    print()

    sprites = discover_sprites()
    if not sprites:
        print("ERROR: No sprites found! Expected: name_1.png name_2.png ...")
        return

    print(f"Found {sum(len(v) for v in sprites.values())} frames in {len(sprites)} sprites:")
    for name, frames in sprites.items():
        print(f"  {name}: {len(frames)} frames ({[f[0] for f in frames]})")

    # Process sprites
    sprites_data = {}
    total_bytes = 0
    for name, files in sprites.items():
        sprites_data[name] = []
        for frame_num, filepath in files:
            img = Image.open(filepath)
            img = img.resize(SPRITE_SIZE, Image.LANCZOS)
            pixels, w, h = pil_to_rgb565(img)
            sprites_data[name].append((pixels, w, h))
            total_bytes += len(pixels)
            print(f"  {name}_{frame_num}: {len(pixels)} bytes")
            img.close()

    print(f"\nTotal: {total_bytes} bytes ({total_bytes/1024:.1f} KB)")

    # Generate header
    header = generate_header(sprites_data)
    header_path = os.path.join(OUTPUT_DIR, "sprites.h")
    with open(header_path, "w") as f:
        f.write(header)
    print(f"\nGenerated: {header_path} ({len(header)} bytes)")

    # Generate impl
    impl = generate_impl(sprites_data)
    impl_path = os.path.join(OUTPUT_DIR, "sprites_render.cpp")
    with open(impl_path, "w") as f:
        f.write(impl)
    print(f"Generated: {impl_path} ({len(impl)} bytes)")

    print("\nDone! Ready to compile.")

if __name__ == "__main__":
    main()
