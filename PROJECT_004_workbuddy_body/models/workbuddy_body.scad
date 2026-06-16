// ============================================================
// WorkBuddy Body — 3D Printable Enclosure
// ============================================================
// A friendly desk companion body for WorkBuddy AI Assistant.
// Fits: ESP32-C3 SuperMini + ST7789 1.54" 240x240 TFT LCD
//
// Print Settings:
//   Material: PLA or PETG (orange recommended for body)
//   Layer height: 0.15–0.20mm
//   Infill: 15% gyroid
//   Supports: YES (for display window overhang & antenna)
//   Orientation: Front face DOWN on build plate
//
// License: MIT (code) / CC BY-NC-SA 4.0 (model)
// ============================================================

use <./libs/rounded_box.scad>  // optional, fallback inline

// ==================== PARAMETERS ====================

// --- Body ---
body_w       = 52;    // Body outer width (X)
body_h       = 58;    // Body outer height (Y)
body_d       = 22;    // Body outer depth (Z)
wall_t       = 2.0;   // Wall thickness
corner_r     = 4;     // Corner rounding radius
base_taper   = 1.5;   // Extra width at base for stability

// --- Display Module (ST7789 1.54" 240x240) ---
disp_pcb_w   = 37;    // Display PCB width
disp_pcb_h   = 37;    // Display PCB height
disp_pcb_t   = 3.5;   // Display PCB + component thickness
disp_active  = 27.8;  // Active display area (square)
disp_window  = 29;    // Window cutout (with 0.6mm margin each side)
disp_lip     = 1.5;   // Lip width to hold display module
disp_y_off   = 2;     // Display offset UP from center

// --- M2 Screw Posts (for display bracket) ---
screw_r      = 1.0;   // M2 screw hole radius
screw_post_r = 2.5;   // Screw post outer radius
screw_dist_x = 30;    // Distance between screw posts (X)
screw_dist_y = 33;    // Distance between screw posts (Y)

// --- Ear Bumps ---
ear_d        = 10;    // Ear bump diameter
ear_h        = 5;     // Ear protrusion from body side
ear_y_off    = 0;     // Ear vertical offset from center

// --- Antenna Dot ---
antenna_d    = 8;     // Antenna bump diameter
antenna_h    = 6;     // Antenna height above body top

// --- USB-C Cable Exit ---
usb_w        = 10;    // USB-C slot width
usb_h        = 5;     // USB-C slot height

// --- ESP32-C3 SuperMini Mounting ---
esp_w        = 22.5;  // ESP32 PCB width
esp_h        = 18;    // ESP32 PCB height
esp_usb_ext  = 3;     // USB connector extends beyond PCB edge

// --- Back Plate ---
back_t       = 1.5;   // Back plate thickness
clip_w       = 4;     // Snap clip width
clip_h       = 3;     // Snap clip height
clip_d       = 1.2;   // Snap clip depth (protrusion)
clip_clear   = 0.3;   // Clearance for snap fit

// ==================== RENDER CONTROL ====================
// Set to "front" for front shell, "back" for back plate, "both" for both
render_part = "both";  // "front" | "back" | "both"

$fn = 48;  // Facet count for curves

// ==================== HELPER MODULES ====================

module rounded_box(w, h, d, r) {
    // Rounded rectangular prism
    hull() {
        translate([-w/2+r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([ w/2-r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([-w/2+r,  h/2-r, 0]) cylinder(r=r, h=d);
        translate([ w/2-r,  h/2-r, 0]) cylinder(r=r, h=d);
    }
}

module rounded_box_tapered(w_top, w_bot, h, d, r) {
    // Box wider at bottom for stability
    hull() {
        // Bottom face (wider)
        translate([-w_bot/2+r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([ w_bot/2-r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([-w_bot/2+r,  h/2-r, 0]) cylinder(r=r, h=d);
        translate([ w_bot/2-r,  h/2-r, 0]) cylinder(r=r, h=d);
    }
}

// ==================== FRONT SHELL ====================

module front_shell() {
    difference() {
        union() {
            // Main body (slightly wider at base)
            hull() {
                // Top face
                translate([-body_w/2+corner_r, -body_h/2+corner_r, 0])
                    cylinder(r=corner_r, h=body_d);
                translate([ body_w/2-corner_r, -body_h/2+corner_r, 0])
                    cylinder(r=corner_r, h=body_d);
                translate([-body_w/2+corner_r,  body_h/2-corner_r, 0])
                    cylinder(r=corner_r, h=body_d);
                translate([ body_w/2-corner_r,  body_h/2-corner_r, 0])
                    cylinder(r=corner_r, h=body_d);
            }

            // Left ear
            translate([-body_w/2, ear_y_off, body_d/2])
                rotate([0, 90, 0])
                    cylinder(d=ear_d, h=ear_h);

            // Right ear
            translate([body_w/2, ear_y_off, body_d/2])
                rotate([0, -90, 0])
                    cylinder(d=ear_d, h=ear_h);

            // Antenna dot on top
            translate([0, body_h/2 - 4, body_d])
                cylinder(d=antenna_d, h=antenna_h);
        }

        // ---- Cutouts ----

        // Display window (front face, Z=0 side)
        translate([-disp_window/2, -disp_window/2 + disp_y_off, -0.5])
            cube([disp_window, disp_window, wall_t + 1]);

        // Display module cavity (inside, behind the window)
        translate([-disp_pcb_w/2, -disp_pcb_h/2 + disp_y_off, wall_t])
            cube([disp_pcb_w, disp_pcb_h, disp_pcb_t + 2]);

        // Display lip shelf (narrower than cavity, holds the display)
        // The lip is the wall_t thickness around the window
        // The cavity is already cut, the lip is the remaining material

        // Main interior cavity
        translate([
            -body_w/2 + wall_t,
            -body_h/2 + wall_t,
            wall_t + disp_pcb_t + 1
        ])
            cube([
                body_w - 2*wall_t,
                body_h - 2*wall_t,
                body_d - wall_t - disp_pcb_t - 1
            ]);

        // USB-C cable exit slot (bottom edge, back side)
        translate([-usb_w/2, -body_h/2 - 0.5, body_d - usb_h - wall_t])
            cube([usb_w, wall_t + 1, usb_h]);

        // M2 screw holes for display bracket
        for (sx = [-1, 1], sy = [-1, 1]) {
            translate([
                sx * screw_dist_x/2,
                sy * screw_dist_y/2 + disp_y_off,
                wall_t - 1
            ])
                cylinder(r=screw_r, h=wall_t + 2);
        }

        // Wire routing channel (from display area to ESP32 area)
        translate([-3, -body_h/2 + wall_t, wall_t + disp_pcb_t + 1])
            cube([6, body_h - 2*wall_t, 3]);

        // Snap clip slots for back plate (4 positions)
        for (cx = [-1, 1], cy = [-1, 1]) {
            translate([
                cx * (body_w/2 - wall_t - 1),
                cy * (body_h/2 - wall_t - 8) + cy * 4,
                body_d - wall_t - clip_h
            ])
                cube([wall_t + 2, clip_w, clip_h]);
        }

        // Decorative: thin bezel line around display window
        // (subtle groove, 0.5mm deep)
        offset = 1;
        translate([
            -disp_window/2 - offset,
            -disp_window/2 - offset + disp_y_off,
            -0.5
        ])
            cube([disp_window + 2*offset, disp_window + 2*offset, 0.5]);
    }

    // M2 screw posts (internal, behind display)
    for (sx = [-1, 1], sy = [-1, 1]) {
        translate([
            sx * screw_dist_x/2,
            sy * screw_dist_y/2 + disp_y_off,
            wall_t
        ])
            difference() {
                cylinder(r=screw_post_r, h=disp_pcb_t + 1);
                translate([0, 0, -0.5])
                    cylinder(r=screw_r, h=disp_pcb_t + 2);
            }
    }
}

// ==================== BACK PLATE ====================

module back_plate() {
    difference() {
        // Main plate
        hull() {
            translate([-body_w/2+corner_r, -body_h/2+corner_r, 0])
                cylinder(r=corner_r, h=back_t);
            translate([ body_w/2-corner_r, -body_h/2+corner_r, 0])
                cylinder(r=corner_r, h=back_t);
            translate([-body_w/2+corner_r,  body_h/2-corner_r, 0])
                cylinder(r=corner_r, h=back_t);
            translate([ body_w/2-corner_r,  body_h/2-corner_r, 0])
                cylinder(r=corner_r, h=back_t);
        }

        // Snap clip clearance slots
        for (cx = [-1, 1], cy = [-1, 1]) {
            translate([
                cx * (body_w/2 - wall_t - 1),
                cy * (body_h/2 - wall_t - 8) + cy * 4 - clip_w/2,
                -0.5
            ])
                cube([wall_t + 2, clip_w + clip_clear*2, back_t + 1]);
        }
    }

    // Snap clips (4 positions)
    for (cx = [-1, 1], cy = [-1, 1]) {
        translate([
            cx * (body_w/2 - wall_t - 1),
            cy * (body_h/2 - wall_t - 8) + cy * 4,
            back_t
        ])
            // Clip ramp
            difference() {
                cube([clip_d, clip_w, clip_h]);
                translate([0, 0, clip_h])
                    rotate([0, atan(clip_h/clip_d), 0])
                        cube([clip_d*2, clip_w, clip_h*2]);
            }
    }

    // ESP32 mounting guide rails (internal ridges for double-sided tape)
    // Two small ridges to help align the ESP32 board
    for (ex = [-1, 1]) {
        translate([
            ex * (esp_w/2 - 1),
            -body_h/2 + wall_t + 5,
            back_t
        ])
            cube([1.5, body_h - 2*wall_t - 10, 1.5]);
    }
}

// ==================== RENDER ====================

if (render_part == "front" || render_part == "both") {
    front_shell();
}

if (render_part == "back" || render_part == "both") {
    if (render_part == "both") {
        translate([body_w + 10, 0, 0])
            back_plate();
    } else {
        back_plate();
    }
}
