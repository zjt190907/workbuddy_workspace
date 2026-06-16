"""
WorkBuddy Body — STL Generator
Generates front_shell.stl and back_plate.stl from the same parameters as the OpenSCAD model.
Uses trimesh + manifold3d for boolean CSG operations.
"""

import trimesh
import numpy as np
import os

OUTPUT_DIR = r"D:\workBuddy_workspace\PROJECT_004_workbuddy_body\models"

# ==================== PARAMETERS ====================
# Must match workbuddy_body.scad exactly

body_w     = 52.0
body_h     = 58.0
body_d     = 22.0
wall_t     = 2.0
corner_r   = 4.0

disp_pcb_w = 37.0
disp_pcb_h = 37.0
disp_pcb_t = 3.5
disp_window= 29.0
disp_y_off = 2.0

screw_r      = 1.0
screw_post_r = 2.5
screw_dist_x = 30.0
screw_dist_y = 33.0

ear_d      = 10.0
ear_h      = 5.0
ear_y_off  = 0.0

antenna_d  = 8.0
antenna_h  = 6.0

usb_w      = 10.0
usb_h      = 5.0

esp_w      = 22.5
esp_h      = 18.0

back_t     = 1.5
clip_w     = 4.0
clip_h     = 3.0
clip_d     = 1.2
clip_clear = 0.3

CYL_SEGS = 32  # Cylinder segments (matches $fn=48 roughly)

# ==================== HELPERS ====================

def rounded_box_mesh(w, h, d, r, segments=CYL_SEGS):
    """Create a rounded rectangular box using convex hull of 4 cylinders."""
    # Create 4 cylinders at corners and hull them
    cyls = []
    positions = [
        (-w/2 + r, -h/2 + r),
        ( w/2 - r, -h/2 + r),
        (-w/2 + r,  h/2 - r),
        ( w/2 - r,  h/2 - r),
    ]
    for px, py in positions:
        c = trimesh.primitives.Cylinder(radius=r, height=d, sections=segments)
        # Translate cylinder: trimesh cylinders are centered at origin along Z
        c.apply_translation([px, py, d/2])
        cyls.append(c)

    result = cyls[0]
    for c in cyls[1:]:
        result = result.union(c)
    return result

def box_mesh(w, h, d):
    """Create a simple box, origin at corner (0,0,0)."""
    return trimesh.primitives.Box(extents=[w, h, d])

def cylinder_mesh(r, h, segments=CYL_SEGS):
    """Create a cylinder centered at origin along Z, bottom at z=0."""
    c = trimesh.primitives.Cylinder(radius=r, height=h, sections=segments)
    c.apply_translation([0, 0, h/2])
    return c

# ==================== FRONT SHELL ====================

def make_front_shell():
    print("  Building main body...")
    body = rounded_box_mesh(body_w, body_h, body_d, corner_r)

    # Left ear
    print("  Adding ears...")
    left_ear = trimesh.primitives.Cylinder(radius=ear_d/2, height=ear_h, sections=CYL_SEGS)
    left_ear.apply_translation([-body_w/2 - ear_h/2, ear_y_off, body_d/2])
    # Rotate ear to point outward along X
    # Actually, cylinder is along Z, need to rotate to X
    left_ear_rot = left_ear.copy()
    # Rotate 90° around Y axis
    angle = np.pi / 2
    rot = trimesh.transformations.rotation_matrix(angle, [0, 1, 0], [0, 0, 0])
    left_ear_rot.apply_transform(rot)
    left_ear_rot.apply_translation([-body_w/2, ear_y_off, body_d/2])

    right_ear_rot = left_ear.copy()
    right_ear_rot.apply_transform(rot)
    right_ear_rot.apply_translation([body_w/2, ear_y_off, body_d/2])

    # Antenna on top
    print("  Adding antenna...")
    antenna = trimesh.primitives.Cylinder(radius=antenna_d/2, height=antenna_h, sections=CYL_SEGS)
    antenna.apply_translation([0, body_h/2 - 4, body_d + antenna_h/2])

    # Union body + ears + antenna
    print("  Union body parts...")
    shell = body.union(left_ear_rot).union(right_ear_rot).union(antenna)

    # --- CUTOUTS ---
    print("  Cutting display window...")
    # Display window (front face, Z=0 side)
    dw = box_mesh(disp_window, disp_window, wall_t + 1)
    dw.apply_translation([-disp_window/2, -disp_window/2 + disp_y_off, -0.5])
    shell = shell.difference(dw)

    # Display module cavity
    print("  Cutting display cavity...")
    dc = box_mesh(disp_pcb_w, disp_pcb_h, disp_pcb_t + 2)
    dc.apply_translation([-disp_pcb_w/2, -disp_pcb_h/2 + disp_y_off, wall_t])
    shell = shell.difference(dc)

    # Main interior cavity
    print("  Cutting interior cavity...")
    inner_w = body_w - 2 * wall_t
    inner_h = body_h - 2 * wall_t
    inner_d = body_d - wall_t - disp_pcb_t - 1
    inner_z = wall_t + disp_pcb_t + 1
    ic = box_mesh(inner_w, inner_h, inner_d)
    ic.apply_translation([-body_w/2 + wall_t, -body_h/2 + wall_t, inner_z])
    shell = shell.difference(ic)

    # USB-C slot
    print("  Cutting USB-C slot...")
    usb = box_mesh(usb_w, wall_t + 1, usb_h)
    usb.apply_translation([-usb_w/2, -body_h/2 - 0.5, body_d - usb_h - wall_t])
    shell = shell.difference(usb)

    # Screw holes
    print("  Cutting screw holes...")
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            sh = trimesh.primitives.Cylinder(radius=screw_r, height=wall_t + 2, sections=16)
            sh.apply_translation([
                sx * screw_dist_x / 2,
                sy * screw_dist_y / 2 + disp_y_off,
                wall_t - 1 + (wall_t + 2) / 2
            ])
            shell = shell.difference(sh)

    # Wire routing channel
    print("  Cutting wire channel...")
    wc = box_mesh(6, inner_h, 3)
    wc.apply_translation([-3, -body_h/2 + wall_t, inner_z])
    shell = shell.difference(wc)

    # Snap clip slots (4 positions)
    print("  Cutting clip slots...")
    for cx in [-1, 1]:
        for cy in [-1, 1]:
            cs = box_mesh(wall_t + 2, clip_w, clip_h)
            cs.apply_translation([
                cx * (body_w/2 - wall_t - 1),
                cy * (body_h/2 - wall_t - 8) + cy * 4,
                body_d - wall_t - clip_h
            ])
            shell = shell.difference(cs)

    # Bezel groove
    print("  Cutting bezel groove...")
    offset = 1.0
    bz = box_mesh(disp_window + 2*offset, disp_window + 2*offset, 0.5)
    bz.apply_translation([
        -disp_window/2 - offset,
        -disp_window/2 - offset + disp_y_off,
        -0.5
    ])
    shell = shell.difference(bz)

    # Screw posts (add material)
    print("  Adding screw posts...")
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            post = trimesh.primitives.Cylinder(radius=screw_post_r, height=disp_pcb_t + 1, sections=16)
            post.apply_translation([
                sx * screw_dist_x / 2,
                sy * screw_dist_y / 2 + disp_y_off,
                wall_t + (disp_pcb_t + 1) / 2
            ])
            hole = trimesh.primitives.Cylinder(radius=screw_r, height=disp_pcb_t + 2, sections=16)
            hole.apply_translation([
                sx * screw_dist_x / 2,
                sy * screw_dist_y / 2 + disp_y_off,
                wall_t - 0.5 + (disp_pcb_t + 2) / 2
            ])
            post_with_hole = post.difference(hole)
            shell = shell.union(post_with_hole)

    return shell

# ==================== BACK PLATE ====================

def make_back_plate():
    print("  Building back plate...")
    plate = rounded_box_mesh(body_w, body_h, back_t, corner_r)

    # Snap clip clearance slots
    print("  Cutting clip slots...")
    for cx in [-1, 1]:
        for cy in [-1, 1]:
            cs = box_mesh(wall_t + 2, clip_w + clip_clear * 2, back_t + 1)
            cs.apply_translation([
                cx * (body_w/2 - wall_t - 1),
                cy * (body_h/2 - wall_t - 8) + cy * 4 - clip_w/2,
                -0.5
            ])
            plate = plate.difference(cs)

    # Snap clips (4 positions) - simple rectangular blocks
    print("  Adding snap clips...")
    for cx in [-1, 1]:
        for cy in [-1, 1]:
            clip = box_mesh(clip_d, clip_w, clip_h)
            clip.apply_translation([
                cx * (body_w/2 - wall_t - 1),
                cy * (body_h/2 - wall_t - 8) + cy * 4,
                back_t
            ])
            plate = plate.union(clip)

    # ESP32 mounting guide rails
    print("  Adding ESP32 guide rails...")
    for ex in [-1, 1]:
        rail = box_mesh(1.5, body_h - 2 * wall_t - 10, 1.5)
        rail.apply_translation([
            ex * (esp_w/2 - 1),
            -body_h/2 + wall_t + 5,
            back_t
        ])
        plate = plate.union(rail)

    return plate

# ==================== MAIN ====================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 50)
    print("WorkBuddy Body — STL Generator")
    print("=" * 50)

    print("\n[1/2] Generating front shell...")
    front = make_front_shell()
    front_path = os.path.join(OUTPUT_DIR, "front_shell.stl")
    print(f"  Exporting {front_path}...")
    front.export(front_path)
    print(f"  Vertices: {len(front.vertices)}, Faces: {len(front.faces)}")
    print(f"  Volume: {front.volume:.1f} mm³")

    print("\n[2/2] Generating back plate...")
    back = make_back_plate()
    back_path = os.path.join(OUTPUT_DIR, "back_plate.stl")
    print(f"  Exporting {back_path}...")
    back.export(back_path)
    print(f"  Vertices: {len(back.vertices)}, Faces: {len(back.faces)}")
    print(f"  Volume: {back.volume:.1f} mm³")

    print("\n" + "=" * 50)
    print("Done! STL files exported to:")
    print(f"  {front_path}")
    print(f"  {back_path}")
    print("=" * 50)

if __name__ == "__main__":
    main()
