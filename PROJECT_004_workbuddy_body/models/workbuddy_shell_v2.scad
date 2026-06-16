// ============================================================
// WorkBuddy "Yi" (一) — Shell V2 — Character Enclosure
// ============================================================
// A friendly AI desk companion with personality.
// Fits: ESP32-C3 SuperMini + ST7789 1.54" 240x240 TFT LCD
//
// Design philosophy:
//   - Minimalist, rounded, approachable
//   - Twin sensor "ears" on top for character
//   - Slightly tapered body for stability
//   - Display recessed into a sculpted faceplate
//   - Subtle vent lines on sides for visual texture
//
// Print Settings:
//   PLA or PETG, 0.15mm layer height, 15% gyroid infill
//   Supports: YES for display window bridge (tree supports)
//   Orientation: Front face DOWN on build plate
// ============================================================

// ==================== PARAMETERS ====================

// --- Global ---
$fn = 64;  // Smooth curves

// --- Body Dimensions ---
body_w       = 50;     // Body width (X)
body_h       = 64;     // Body height (Y) — taller for character proportions
body_d       = 24;     // Body depth (Z)
wall_t       = 2.2;    // Wall thickness
corner_r     = 6;      // Corner radius — softer, friendlier
base_flare   = 3;      // Extra width per side at very bottom

// --- Display (ST7789 1.54" 240x240) ---
disp_pcb_w   = 37;     // PCB width
disp_pcb_h   = 37;     // PCB height
disp_pcb_t   = 3.5;    // PCB + component total thickness
disp_active  = 27.8;   // Active area (square)
disp_window  = 29;     // Window cutout
disp_lip     = 1.8;    // Retention lip for display
disp_y_off   = -2;     // Display slightly higher on face

// --- Ears (Twin sensor bumps on top) ---
ear_w        = 8;      // Ear width
ear_h        = 10;     // Ear height above body
ear_d        = 4;      // Ear depth (Z)
ear_angle    = 25;     // Ear outward angle from vertical
ear_spread   = 16;     // Distance from center to ear base

// --- Feet (base stability bumps) ---
foot_w       = 8;
foot_d       = 4;
foot_h       = 2;

// --- USB-C Exit ---
usb_w        = 12;     // USB-C slot width
usb_h        = 6;      // USB-C slot height

// --- ESP32 Mounting ---
esp_pcb_w    = 22.5;
esp_pcb_h    = 18;
esp_pcb_t    = 6;      // PCB + components + USB protrusion

// --- Back Plate ---
back_t       = 1.8;
clip_w       = 5;
clip_h       = 2.5;
clip_d       = 1.5;
clip_clear   = 0.25;
clip_count   = 4;      // 2 per side

// --- Decorative ---
vent_slot_w  = 2;
vent_slot_h  = 10;
vent_slot_gap = 3;
vent_count   = 3;      // Vents per side

// --- Screw Posts (M2 for display bracket) ---
screw_r       = 1.1;   // M2 clearance hole
screw_post_r  = 2.8;
screw_dist_x  = 30;
screw_dist_y  = 33;

// ==================== RENDER CONTROL ====================
render_part = "both";  // "front" | "back" | "both"

// ==================== HELPER MODULES ====================

module rounded_cube(w, h, d, r) {
    hull() {
        translate([-w/2+r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([ w/2-r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([-w/2+r,  h/2-r, 0]) cylinder(r=r, h=d);
        translate([ w/2-r,  h/2-r, 0]) cylinder(r=r, h=d);
    }
}

module ear_pair() {
    for (sx = [-1, 1]) {
        translate([sx * ear_spread, body_h/2 - 2, body_d/2])
            rotate([0, 90, sx * ear_angle])
                scale([1, 1, 0.5])
                    cylinder(d=ear_w, h=ear_h, center=true);
    }
}

module vent_slots() {
    for (sx = [-1, 1]) {
        for (i = [0 : vent_count - 1]) {
            translate([
                sx * (body_w/2 - wall_t - 0.5),
                -body_h/4 + i * (vent_slot_h + vent_slot_gap),
                body_d/2
            ])
                rotate([0, 90, 0])
                    cylinder(r=vent_slot_w/2, h=wall_t + 1, center=true);
        }
    }
}

module bezel_groove() {
    // Decorative groove around display window
    offset = 2.5;
    union() {
        // Top
        translate([-disp_window/2 - offset,  disp_window/2 + disp_y_off + offset, -0.6])
            cube([disp_window + 2*offset, 1.5, 1.2]);
        // Bottom
        translate([-disp_window/2 - offset, -disp_window/2 + disp_y_off - offset - 0.5, -0.6])
            cube([disp_window + 2*offset, 2.5, 1.2]);
        // Left
        translate([-disp_window/2 - offset, -disp_window/2 + disp_y_off - offset, -0.6])
            cube([1.5, disp_window + 2*offset, 1.2]);
        // Right
        translate([ disp_window/2 + offset - 0.5, -disp_window/2 + disp_y_off - offset, -0.6])
            cube([2.5, disp_window + 2*offset, 1.2]);
    }
}

// ==================== FRONT SHELL ====================

module front_shell() {
    difference() {
        union() {
            // === Main body ===
            rounded_cube(body_w, body_h, body_d, corner_r);

            // === Ears ===
            ear_pair();

            // === Base feet ===
            for (fx = [-1, 1]) {
                translate([fx * (body_w/2 - foot_w/2 - 3), -body_h/2 + 2, -foot_h])
                    rounded_cube(foot_w, 6, foot_h + 0.1, 2);
            }
        }

        // === Interior Cavity ===
        translate([0, 0, wall_t + disp_pcb_t + 2])
            rounded_cube(
                body_w - 2*wall_t,
                body_h - 2*wall_t + 2,
                body_d - wall_t - disp_pcb_t,
                corner_r - wall_t
            );

        // === Display Window ===
        translate([-disp_window/2, -disp_window/2 + disp_y_off, -0.5])
            cube([disp_window, disp_window, wall_t + 1.5]);

        // === Display PCB Cavity ===
        translate([-disp_pcb_w/2, -disp_pcb_h/2 + disp_y_off, wall_t])
            cube([disp_pcb_w, disp_pcb_h, disp_pcb_t + 1]);

        // === USB-C Exit (bottom-back) ===
        translate([-usb_w/2, -body_h/2 - 0.5, body_d - usb_h - wall_t + 1])
            cube([usb_w, wall_t + 1, usb_h]);

        // === M2 Screw Holes (display mount) ===
        for (sx = [-1, 1], sy = [-1, 1]) {
            translate([
                sx * screw_dist_x/2,
                sy * screw_dist_y/2 + disp_y_off,
                -0.5
            ])
                cylinder(r=screw_r, h=wall_t + 2);
        }

        // === Wire Channel ===
        translate([-4, -body_h/2 + wall_t, wall_t + disp_pcb_t + 1])
            cube([8, body_h - 2*wall_t, 3]);

        // === Snap Clip Pockets (for back plate) ===
        for (cx = [-1, 1], i = [0, 1]) {
            cy = i * 2 - 1;  // -1 or +1
            translate([
                cx * (body_w/2 - wall_t - 1),
                cy * (body_h/3),
                body_d - wall_t - clip_h
            ])
                cube([wall_t + 2, clip_w, clip_h]);
        }

        // === Vent Slots ===
        vent_slots();

        // === Bezel Groove ===
        bezel_groove();
    }

    // === Internal: M2 Screw Posts ===
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

    // === Internal: ESP32 Alignment Rails ===
    for (sx = [-1, 1]) {
        translate([
            sx * (esp_pcb_w/2 + 1),
            -body_h/2 + wall_t + 8,
            body_d - wall_t - esp_pcb_t
        ])
            cube([1.5, esp_pcb_h + 4, esp_pcb_t]);
    }
}

// ==================== BACK PLATE ====================

module back_plate() {
    union() {
        difference() {
            // Main plate
            rounded_cube(body_w, body_h, back_t, corner_r - 0.5);

            // Snap clip clearance slots
            for (cx = [-1, 1], i = [0, 1]) {
                cy = i * 2 - 1;
                translate([
                    cx * (body_w/2 - wall_t - 1),
                    cy * (body_h/3) - clip_w/2 - clip_clear,
                    -0.5
                ])
                    cube([wall_t + 2, clip_w + clip_clear*2, back_t + 1]);
            }
        }

        // Snap clip tabs
        for (cx = [-1, 1], i = [0, 1]) {
            cy = i * 2 - 1;
            translate([
                cx * (body_w/2 - wall_t - 1),
                cy * (body_h/3),
                back_t
            ])
                difference() {
                    cube([clip_d, clip_w, clip_h]);
                    translate([-clip_d*0.3, 0, clip_h])
                        rotate([0, 30, 0])
                            cube([clip_d*2, clip_w, clip_h*2]);
                }
        }

        // ESP32 alignment ridges
        for (sx = [-1, 1]) {
            translate([
                sx * (esp_pcb_w/2 + 1),
                -body_h/2 + wall_t + 8,
                back_t
            ])
                cube([1.5, esp_pcb_h + 4, 1.5]);
        }

        // Ventilation grill on back (matching front vents)
        for (i = [0 : vent_count - 1]) {
            translate([
                0,
                -body_h/4 + i * (vent_slot_h + vent_slot_gap),
                -0.5
            ])
                cube([vent_slot_w, vent_slot_h, back_t + 1]);
        }
    }
}

// ==================== RENDER ====================

if (render_part == "front" || render_part == "both") {
    front_shell();
}

if (render_part == "back" || render_part == "both") {
    if (render_part == "both") {
        translate([body_w + 15, 0, 0])
            back_plate();
    } else {
        back_plate();
    }
}
