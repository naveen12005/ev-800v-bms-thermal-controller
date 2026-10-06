"""
Battery Module Assembly (12S2P Prismatic Architecture)
======================================================
Vehicle System: 800V High-Power EV Battery Pack (Sub-Module Brick)

Components in Assembly:
- 24x Prismatic Lithium-Ion Cells (148 x 27 x 91 mm, VDA / CATL standard format)
- 1x High-Performance TIM Gap Pad (1.0 mm thickness, k = 3.5 W/m.K)
- 2x Structural Aluminum End Compression Plates with Tie Rods
- Laser-welded Copper Busbar interconnects (Series-Parallel 12S2P)
- Base Cold Plate Mounting Interface
"""

import math
import os

CELL_WIDTH = 148.0      # mm (transverse X)
CELL_THICKNESS = 27.0   # mm (longitudinal Y)
CELL_HEIGHT = 91.0      # mm (vertical Z)
CELL_MASS_KG = 0.88     # kg per cell (~3.7V nominal, ~52Ah)

NUM_SERIES = 12
NUM_PARALLEL = 2
TOTAL_CELLS = NUM_SERIES * NUM_PARALLEL  # 24 cells

TIM_THICKNESS = 1.0     # mm
END_PLATE_THICKNESS = 15.0 # mm (compression plate)
PLATE_BASE_Z = 12.0     # mm (cold plate top surface)

def generate_module_stl(output_stl_path="cad/battery_module_12s2p_assembly.stl"):
    vertices = []
    triangles = []

    def add_box(x0, y0, z0, dx, dy, dz):
        v_start = len(vertices)
        box_v = [
            (x0, y0, z0),          # 0
            (x0 + dx, y0, z0),     # 1
            (x0 + dx, y0 + dy, z0),# 2
            (x0, y0 + dy, z0),     # 3
            (x0, y0, z0 + dz),     # 4
            (x0 + dx, y0, z0 + dz),# 5
            (x0 + dx, y0 + dy, z0 + dz), # 6
            (x0, y0 + dy, z0 + dz) # 7
        ]
        vertices.extend(box_v)
        faces = [
            (0, 1, 2), (0, 2, 3), # Bottom
            (4, 6, 5), (4, 7, 6), # Top
            (0, 5, 1), (0, 4, 5), # Front
            (2, 7, 3), (2, 6, 7), # Back
            (0, 3, 7), (0, 7, 4), # Left
            (1, 5, 6), (1, 6, 2)  # Right
        ]
        for f in faces:
            triangles.append((v_start + f[0], v_start + f[1], v_start + f[2]))

    # 1. TIM Pad Layer (between cold plate and cell bottoms)
    add_box(15.0, 15.0, PLATE_BASE_Z, 330.0, 300.0, TIM_THICKNESS)

    z_cells_start = PLATE_BASE_Z + TIM_THICKNESS

    # 2. 24 Prismatic Cells arranged in 2 columns of 12 rows
    cell_gap = 1.5  # aerogel / mica thermal insulation spacer (mm)
    col_gap = 10.0  # center spine partition (mm)
    x_col0 = 20.0
    x_col1 = x_col0 + CELL_WIDTH + col_gap

    for row in range(12):
        y_pos = 20.0 + row * (CELL_THICKNESS + cell_gap)
        # Column 0 cell
        add_box(x_col0, y_pos, z_cells_start, CELL_WIDTH, CELL_THICKNESS, CELL_HEIGHT)
        # Column 1 cell
        add_box(x_col1, y_pos, z_cells_start, CELL_WIDTH, CELL_THICKNESS, CELL_HEIGHT)
        # Copper Terminal Terminals (Positive and Negative studs on top)
        add_box(x_col0 + 20.0, y_pos + 6.0, z_cells_start + CELL_HEIGHT, 15.0, 15.0, 6.0)
        add_box(x_col0 + CELL_WIDTH - 35.0, y_pos + 6.0, z_cells_start + CELL_HEIGHT, 15.0, 15.0, 6.0)
        add_box(x_col1 + 20.0, y_pos + 6.0, z_cells_start + CELL_HEIGHT, 15.0, 15.0, 6.0)
        add_box(x_col1 + CELL_WIDTH - 35.0, y_pos + 6.0, z_cells_start + CELL_HEIGHT, 15.0, 15.0, 6.0)

    # 3. Structural End Compression Plates
    y_front_end = 20.0 - END_PLATE_THICKNESS - 2.0
    y_rear_end = 20.0 + 12 * (CELL_THICKNESS + cell_gap) + 2.0
    mod_total_width = 2 * CELL_WIDTH + col_gap + 20.0

    add_box(15.0, y_front_end, z_cells_start - TIM_THICKNESS, mod_total_width, END_PLATE_THICKNESS, CELL_HEIGHT + 10.0)
    add_box(15.0, y_rear_end, z_cells_start - TIM_THICKNESS, mod_total_width, END_PLATE_THICKNESS, CELL_HEIGHT + 10.0)

    # Write ASCII STL
    with open(output_stl_path, "w") as f:
        f.write("solid Battery_Module_12S2P_Assembly\n")
        for tri in triangles:
            v0 = vertices[tri[0]]
            v1 = vertices[tri[1]]
            v2 = vertices[tri[2]]
            ux, uy, uz = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
            vx, vy, vz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            mag = math.sqrt(nx*nx + ny*ny + nz*nz) or 1.0
            nx, ny, nz = nx/mag, ny/mag, nz/mag

            f.write(f"  facet normal {nx:.4e} {ny:.4e} {nz:.4e}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v0[0]:.4f} {v0[1]:.4f} {v0[2]:.4f}\n")
            f.write(f"      vertex {v1[0]:.4f} {v1[1]:.4f} {v1[2]:.4f}\n")
            f.write(f"      vertex {v2[0]:.4f} {v2[1]:.4f} {v2[2]:.4f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid Battery_Module_12S2P_Assembly\n")

    print(f"12S2P Battery Module CAD Assembly STL exported: {output_stl_path} ({len(triangles)} facets)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    generate_module_stl(os.path.join(base_dir, "battery_module_12s2p_assembly.stl"))
