// ============================================================
// WorkBuddy Shell V3 — Minimalist Monolith
// ============================================================
// "I am software. I speak through the screen."
//
// Design philosophy:
//   - Pure geometry — a frame for the digital window
//   - No ears, no antenna, no vents — nothing unnecessary
//   - Slight bottom taper for stance
//   - Single subtle accent beneath display
//   - Clean back plate with invisible snap fit
//
// Fits: ESP32-C3 SuperMini + ST7789 1.54" 240x240 TFT
// ============================================================

$fn = 64;

// ==================== DIMENSIONS ====================

// Body — compact, display-centered
body_w       = 44;     // width
body_h       = 52;     // height
body_d       = 18;     // depth
wall_t       = 2.0;    // wall thickness
corner_r     = 5;      // outer corner radius
base_taper   = 1.5;    // bottom flare per side for stance

// Display module (ST7789 1.54")
disp_pcb_w   = 37;
disp_pcb_h   = 37;
disp_pcb_t   = 3.5;
disp_window  = 29;     // window cutout
disp_lip     = 2.0;    // retention lip depth
disp_y_off   = -1;     // display slightly above center

// Accent — subtle indicator beneath display
accent_w     = 12;
accent_h     = 1.5;
accent_depth = 0.8;

// Screw posts (M2)
screw_r      = 1.1;
screw_post_r = 2.6;
screw_x      = 30;
screw_y      = 33;

// USB-C exit
usb_w        = 11;
usb_h        = 5.5;

// ESP32
esp_w        = 22.5;
esp_h        = 18;
esp_t        = 6;

// Back plate
back_t       = 1.6;
clip_w       = 5;
clip_h       = 2.2;
clip_d       = 1.3;
clip_clear   = 0.2;

// ==================== RENDER ====================
render_part = "both";  // "front" | "back" | "both"

// ==================== HELPERS ====================

module rcuboid(w, h, d, r) {
    hull() {
        translate([-w/2+r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([ w/2-r, -h/2+r, 0]) cylinder(r=r, h=d);
        translate([-w/2+r,  h/2-r, 0]) cylinder(r=r, h=d);
        translate([ w/2-r,  h/2-r, 0]) cylinder(r=r, h=d);
    }
}

module tapered_body() {
    // Wider at bottom for natural stance
    hull() {
        // Top (narrower)
        translate([0, 0, body_d])
            rcuboid(body_w, body_h, 0.01, corner_r);
        // Bottom (wider)
        translate([0, 0, 0])
            rcuboid(body_w + base_taper*2, body_h, 0.01, corner_r);
    }
}

// ==================== FRONT SHELL ====================

module front_shell() {
    difference() {
        union() {
            // Tapered body
            tapered_body();
        }

        // === Display window ===
        translate([-disp_window/2, -disp_window/2 + disp_y_off, -0.5])
            cube([disp_window, disp_window, wall_t + 1.5]);

        // === Display PCB cavity ===
        translate([-disp_pcb_w/2, -disp_pcb_h/2 + disp_y_off, wall_t])
            cube([disp_pcb_w, disp_pcb_h, disp_pcb_t + 2]);

        // === Interior ===
        translate([0, 0, wall_t + disp_pcb_t + 2])
            rcuboid(
                body_w - wall_t*2,
                body_h - wall_t*2 + 4,
                body_d - wall_t - disp_pcb_t,
                corner_r - wall_t
            );

        // === USB-C exit (bottom, rear) ===
        translate([-usb_w/2, -body_h/2 - base_taper - 0.5, body_d - usb_h - wall_t + 1.5])
            cube([usb_w, wall_t + base_taper + 1, usb_h]);

        // === M2 screw holes ===
        for (sx = [-1, 1], sy = [-1, 1]) {
            translate([
                sx * screw_x/2,
                sy * screw_y/2 + disp_y_off,
                -0.5
            ])
                cylinder(r=screw_r, h=wall_t + 2);
        }

        // === Wire channel ===
        translate([-4, -body_h/2 + wall_t, wall_t + disp_pcb_t + 1])
            cube([8, body_h - wall_t*2, 3]);

        // === Snap clip pockets (back plate) ===
        for (cx = [-1, 1], i = [0, 1]) {
            translate([
                cx * (body_w/2 - wall_t - 1),
                (i * 0.6 - 0.3) * (body_h - wall_t*2),
                body_d - wall_t - clip_h
            ])
                cube([wall_t + 2, clip_w, clip_h]);
        }

        // === Accent groove ===
        translate([
            -accent_w/2,
            -disp_window/2 + disp_y_off - 7,
            -0.5
        ])
            cube([accent_w, accent_h, accent_depth + 0.5]);
    }

    // === Internal: screw posts ===
    for (sx = [-1, 1], sy = [-1, 1]) {
        translate([
            sx * screw_x/2,
            sy * screw_y/2 + disp_y_off,
            wall_t
        ])
            difference() {
                cylinder(r=screw_post_r, h=disp_pcb_t + 1);
                translate([0, 0, -0.5])
                    cylinder(r=screw_r, h=disp_pcb_t + 2);
            }
    }

    // === Internal: ESP32 alignment rails ===
    for (sx = [-1, 1]) {
        translate([
            sx * (esp_w/2 + 1),
            -body_h/2 + wall_t + 6,
            body_d - wall_t - esp_t
        ])
            cube([1.5, esp_h + 6, esp_t]);
    }
}

// ==================== BACK PLATE ====================

module back_plate() {
    difference() {
        union() {
            rcuboid(body_w, body_h, back_t, corner_r - 0.5);
        }

        // Clip clearance
        for (cx = [-1, 1], i = [0, 1]) {
            translate([
                cx * (body_w/2 - wall_t - 1),
                (i * 0.6 - 0.3) * (body_h - wall_t*2) - clip_w/2 - clip_clear,
                -0.5
            ])
                cube([wall_t + 2, clip_w + clip_clear*2, back_t + 1]);
        }
    }

    // === Snap clips ===
    for (cx = [-1, 1], i = [0, 1]) {
        translate([
            cx * (body_w/2 - wall_t - 1),
            (i * 0.6 - 0.3) * (body_h - wall_t*2),
            back_t
        ])
            difference() {
                cube([clip_d, clip_w, clip_h]);
                translate([-clip_d*0.3, 0, clip_h])
                    rotate([0, 30, 0])
                        cube([clip_d*2, clip_w, clip_h*2]);
            }
    }

    // === ESP32 guide ridges ===
    for (sx = [-1, 1]) {
        translate([
            sx * (esp_w/2 + 1),
            -body_h/2 + wall_t + 6,
            back_t
        ])
            cube([1.5, esp_h + 6, 1.2]);
    }
}

// ==================== RENDER ====================

if (render_part == "front" || render_part == "both") {
    front_shell();
}

if (render_part == "back" || render_part == "both") {
    if (render_part == "both") {
        translate([body_w + 12, 0, 0]) back_plate();
    } else {
        back_plate();
    }
}
