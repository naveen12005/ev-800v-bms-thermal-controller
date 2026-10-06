"""
STEP CAD Exporter for 800V EV Battery Pack & Cold Plates
========================================================
Generates ISO 10303-21 STEP (.step / .stp) B-Rep CAD geometry for:
1. Baseline Serpentine Liquid Cold Plate
2. Optimized Parallel Microchannel Cold Plate (with dual balanced manifolds)
3. 12S2P Battery Module Assembly (24 Prismatic Cells + TIM + Compression Plates)

Format: Standard STEP AP214 / AP203 readable directly by Siemens NX Design Center Student Edition.
"""

import cadquery as cq
import math
import os
import time

def build_baseline_serpentine_step(output_path):
    print("Building Baseline Serpentine Cold Plate B-Rep Solid...")
    plate_len = 360.0
    plate_wid = 330.0
    plate_thk = 12.0
    ch_w = 14.0
    ch_d = 7.0
    margin = 20.0
    num_passes = 6

    # 1. Base solid block
    plate = cq.Workplane("XY").box(plate_len, plate_wid, plate_thk, centered=(True, True, False))

    # 2. Serpentine passes cut into top surface
    y_pitch = (plate_wid - 2 * margin) / num_passes
    x_span = plate_len - 2 * margin

    for i in range(num_passes):
        y_center = -plate_wid/2.0 + margin + (i + 0.5) * y_pitch
        # Cut longitudinal pass
        cut_pass = (
            cq.Workplane("XY")
            .workplane(offset=plate_thk - ch_d)
            .transformed(offset=(0, y_center, 0))
            .box(x_span, ch_w, ch_d, centered=(True, True, False))
        )
        plate = plate.cut(cut_pass)

    # 3. Cut alternating 180° return bends
    for i in range(num_passes - 1):
        y_turn_center = -plate_wid/2.0 + margin + (i + 1) * y_pitch
        turn_side = 1 if (i % 2 == 0) else -1
        x_turn = turn_side * (x_span / 2.0 - ch_w / 2.0)
        bend_box = (
            cq.Workplane("XY")
            .workplane(offset=plate_thk - ch_d)
            .transformed(offset=(x_turn, y_turn_center, 0))
            .box(ch_w * 2.0, y_pitch, ch_d, centered=(True, True, False))
        )
        plate = plate.cut(bend_box)

    # 4. Fluid Port Bosses (Inlet & Outlet)
    inlet_boss = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk)
        .transformed(offset=(-x_span/2.0 + 10.0, -plate_wid/2.0 + margin + y_pitch/2.0, 0))
        .circle(8.0).extrude(18.0)
        .faces(">Z").hole(10.0, 25.0)
    )
    outlet_boss = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk)
        .transformed(offset=(x_span/2.0 - 10.0, plate_wid/2.0 - margin - y_pitch/2.0, 0))
        .circle(8.0).extrude(18.0)
        .faces(">Z").hole(10.0, 25.0)
    )
    plate = plate.union(inlet_boss).union(outlet_boss)

    # 5. Perimeter M6 Mounting Counterbores
    holes_x = [-plate_len/2.0 + 10.0, plate_len/2.0 - 10.0]
    holes_y = [-plate_wid/2.0 + 10.0, 0.0, plate_wid/2.0 - 10.0]
    for hx in holes_x:
        for hy in holes_y:
            hole = (
                cq.Workplane("XY")
                .transformed(offset=(hx, hy, 0))
                .circle(3.3).extrude(plate_thk)
            )
            plate = plate.cut(hole)

    cq.exporters.export(plate, output_path)
    print(f"Exported: {output_path}")
    return plate

def build_optimized_microchannel_step(output_path):
    print("Building Optimized Parallel Microchannel Cold Plate B-Rep Solid...")
    plate_len = 360.0
    plate_wid = 330.0
    plate_thk = 12.0
    margin = 15.0
    manifold_w = 25.0
    ch_d = 8.0
    num_ch = 24
    fin_t = 1.8

    # 1. Base solid block
    plate = cq.Workplane("XY").box(plate_len, plate_wid, plate_thk, centered=(True, True, False))

    # 2. Dual Distribution Manifolds (Inlet on Left, Outlet on Right)
    active_y_span = plate_wid - 2 * margin
    x_inlet_manifold = -plate_len/2.0 + margin + manifold_w/2.0
    x_outlet_manifold = plate_len/2.0 - margin - manifold_w/2.0

    inlet_man = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk - ch_d)
        .transformed(offset=(x_inlet_manifold, 0, 0))
        .box(manifold_w, active_y_span, ch_d, centered=(True, True, False))
    )
    outlet_man = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk - ch_d)
        .transformed(offset=(x_outlet_manifold, 0, 0))
        .box(manifold_w, active_y_span, ch_d, centered=(True, True, False))
    )
    plate = plate.cut(inlet_man).cut(outlet_man)

    # 3. Parallel Microchannels between manifolds
    ch_len = plate_len - 2 * margin - 2 * manifold_w
    ch_pitch = active_y_span / num_ch
    ch_w = ch_pitch - fin_t

    for i in range(num_ch):
        y_center = -active_y_span/2.0 + (i + 0.5) * ch_pitch
        micro_ch = (
            cq.Workplane("XY")
            .workplane(offset=plate_thk - ch_d)
            .transformed(offset=(0, y_center, 0))
            .box(ch_len + 4.0, ch_w, ch_d, centered=(True, True, False))
        )
        plate = plate.cut(micro_ch)

    # 4. Fluid Port Bosses
    inlet_boss = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk)
        .transformed(offset=(x_inlet_manifold, -active_y_span/2.0 + 20.0, 0))
        .circle(8.0).extrude(18.0)
        .faces(">Z").hole(10.0, 25.0)
    )
    outlet_boss = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk)
        .transformed(offset=(x_outlet_manifold, active_y_span/2.0 - 20.0, 0))
        .circle(8.0).extrude(18.0)
        .faces(">Z").hole(10.0, 25.0)
    )
    plate = plate.union(inlet_boss).union(outlet_boss)

    # 5. Perimeter M6 Mounting Counterbores
    holes_x = [-plate_len/2.0 + 8.0, 0.0, plate_len/2.0 - 8.0]
    holes_y = [-plate_wid/2.0 + 8.0, plate_wid/2.0 - 8.0]
    for hx in holes_x:
        for hy in holes_y:
            hole = (
                cq.Workplane("XY")
                .transformed(offset=(hx, hy, 0))
                .circle(3.3).extrude(plate_thk)
            )
            plate = plate.cut(hole)

    cq.exporters.export(plate, output_path)
    print(f"Exported: {output_path}")
    return plate

def build_module_assembly_step(output_path):
    print("Building 12S2P Battery Module Assembly B-Rep Solid...")
    plate_len = 360.0
    plate_wid = 330.0
    plate_thk = 12.0
    cell_w = 148.0
    cell_t = 27.0
    cell_h = 91.0
    tim_t = 1.0
    endplate_t = 15.0

    # Base structural plate
    assy = cq.Workplane("XY").box(plate_len, plate_wid, plate_thk, centered=(True, True, False))

    # TIM Layer
    tim = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk)
        .box(330.0, 300.0, tim_t, centered=(True, True, False))
    )
    assy = assy.union(tim)

    z_cell = plate_thk + tim_t

    # 24 Prismatic Cells arranged in 2 columns of 12 rows
    cell_gap = 1.5
    col_gap = 10.0
    x_col0 = -col_gap/2.0 - cell_w/2.0
    x_col1 = col_gap/2.0 + cell_w/2.0

    for r in range(12):
        y_pos = - (12 * (cell_t + cell_gap)) / 2.0 + (r + 0.5) * (cell_t + cell_gap)
        # Cell 1 (Left column)
        c0 = (
            cq.Workplane("XY")
            .workplane(offset=z_cell)
            .transformed(offset=(x_col0, y_pos, 0))
            .box(cell_w, cell_t, cell_h, centered=(True, True, False))
        )
        # Cell 2 (Right column)
        c1 = (
            cq.Workplane("XY")
            .workplane(offset=z_cell)
            .transformed(offset=(x_col1, y_pos, 0))
            .box(cell_w, cell_t, cell_h, centered=(True, True, False))
        )
        # Terminal studs
        t0 = (
            cq.Workplane("XY")
            .workplane(offset=z_cell + cell_h)
            .transformed(offset=(x_col0 - cell_w/4.0, y_pos, 0))
            .circle(6.0).extrude(6.0)
        )
        t1 = (
            cq.Workplane("XY")
            .workplane(offset=z_cell + cell_h)
            .transformed(offset=(x_col1 + cell_w/4.0, y_pos, 0))
            .circle(6.0).extrude(6.0)
        )
        assy = assy.union(c0).union(c1).union(t0).union(t1)

    # Compression End Plates
    y_front = - (12 * (cell_t + cell_gap)) / 2.0 - endplate_t / 2.0 - 2.0
    y_rear = (12 * (cell_t + cell_gap)) / 2.0 + endplate_t / 2.0 + 2.0
    total_w = 2 * cell_w + col_gap + 15.0

    ep_front = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk)
        .transformed(offset=(0, y_front, 0))
        .box(total_w, endplate_t, cell_h + 8.0, centered=(True, True, False))
    )
    ep_rear = (
        cq.Workplane("XY")
        .workplane(offset=plate_thk)
        .transformed(offset=(0, y_rear, 0))
        .box(total_w, endplate_t, cell_h + 8.0, centered=(True, True, False))
    )
    assy = assy.union(ep_front).union(ep_rear)

    cq.exporters.export(assy, output_path)
    print(f"Exported: {output_path}")
    return assy

if __name__ == "__main__":
    import shutil
    t0 = time.time()
    out_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Baseline Serpentine Cold Plate STEP
    base_step = os.path.join(out_dir, "baseline_serpentine_coldplate.step")
    base_stp = os.path.join(out_dir, "baseline_serpentine_coldplate.stp")
    p1 = build_baseline_serpentine_step(base_step)
    shutil.copyfile(base_step, base_stp)
    print(f"Copied: {base_stp}")

    # 2. Optimized Parallel Microchannel Cold Plate STEP
    opt_step = os.path.join(out_dir, "optimized_microchannel_coldplate.step")
    opt_stp = os.path.join(out_dir, "optimized_microchannel_coldplate.stp")
    p2 = build_optimized_microchannel_step(opt_step)
    shutil.copyfile(opt_step, opt_stp)
    print(f"Copied: {opt_stp}")

    # 3. 12S2P Battery Module Assembly STEP
    mod_step = os.path.join(out_dir, "battery_module_12s2p_assembly.step")
    mod_stp = os.path.join(out_dir, "battery_module_12s2p_assembly.stp")
    p3 = build_module_assembly_step(mod_step)
    shutil.copyfile(mod_step, mod_stp)
    print(f"Copied: {mod_stp}")

    print(f"All STEP (.step and .stp) CAD models exported successfully in {time.time() - t0:.2f}s!")
