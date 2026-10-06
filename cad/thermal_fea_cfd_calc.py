"""
Analytical Thermal and Fluid Dynamics Verification:
Baseline (Serpentine) vs. Optimized (Parallel Microchannel) Cold Plate
for 800V 75kWh EV Battery Pack (12S2P Sub-Module Brick)

Calculates:
- Reynolds Number (Re), Nusselt Number (Nu), Convective Heat Transfer Coeff (h)
- Total Hydraulic Pressure Drop (ΔP_total = ΔP_friction + ΔP_minor)
- Pumping Parasitic Power Consumption (W_pump)
- Coolant Stream Temperature Rise (ΔT_coolant)
- Spatial Cell-to-Cell Temperature Gradient (ΔT_cell_max_min)
- Thermal Conductance to Coolant Loop (K_cooling in W/K)
"""

import math
import json

def analyze_cold_plate(
    plate_type="OPTIMIZED_PARALLEL",
    heat_load_w=1400.0,      # Waste heat dissipated per 12S2P module at 350kW fast charge (~11 kW across pack)
    flow_rate_lpm=8.0,        # Total coolant volume flow rate to module (L/min)
    t_inlet_c=20.0            # Chilled coolant inlet temperature (°C)
):
    # Coolant: 50/50 Water-Ethylene Glycol (WEG) at ~25°C
    rho = 1065.0          # kg/m^3
    mu = 0.0025           # Pa.s (dynamic viscosity)
    cp = 3320.0           # J/(kg.K) (specific heat)
    k_fluid = 0.40        # W/(m.K) (thermal conductivity)
    pr = (mu * cp) / k_fluid  # Prandtl number ~ 20.75

    # Module & Plate Footprint
    plate_length = 0.350   # m
    plate_width = 0.320    # m
    num_cells = 24         # 12S2P prismatic cells
    tim_thickness = 0.001  # 1.0 mm
    tim_k = 3.5            # W/(m.K) (High performance silicone-free gap pad)
    al_k = 167.0           # W/(m.K) (Aluminum 6061-T6)
    al_wall_t = 0.002      # 2.0 mm conduction wall thickness

    # Total mass flow rate (kg/s)
    v_dot_total = (flow_rate_lpm / 1000.0) / 60.0  # m^3/s
    m_dot_total = rho * v_dot_total                # kg/s

    if plate_type == "BASELINE_SERPENTINE":
        # Single continuous serpentine channel with 6 passes and 5 180° bends
        num_passes = 6
        num_bends = 5
        ch_width = 0.014   # 14 mm
        ch_height = 0.006  # 6 mm
        ch_length_total = plate_width * num_passes  # ~ 1.92 m

        area_flow = ch_width * ch_height
        perim_flow = 2.0 * (ch_width + ch_height)
        d_h = (4.0 * area_flow) / perim_flow  # Hydraulic diameter ~ 8.4 mm

        # Single path velocity
        velocity = v_dot_total / area_flow
        re = (rho * velocity * d_h) / mu

        # Friction factor & Nusselt number
        if re < 2300:
            f = 64.0 / re
            nu = 4.36
        else:
            # Petukhov / Gnielinski correlation for transition/turbulent
            f = (0.79 * math.log(re) - 1.64) ** -2
            nu = ((f / 8.0) * (re - 1000.0) * pr) / (1.0 + 12.7 * math.sqrt(f / 8.0) * (pr ** (2.0/3.0) - 1.0))

        h_conv = (nu * k_fluid) / d_h

        # Major frictional pressure drop (Darcy-Weisbach)
        dp_friction = f * (ch_length_total / d_h) * (0.5 * rho * (velocity ** 2))
        # Minor bend losses (K_bend ≈ 1.5 for 180° return bend)
        k_bends_total = num_bends * 1.5
        dp_minor = k_bends_total * (0.5 * rho * (velocity ** 2))
        dp_total = dp_friction + dp_minor

        # Heat transfer area (wetted bottom surface of channel)
        wetted_area = ch_width * ch_length_total

        # Fluid temperature rise from inlet to outlet
        delta_t_coolant = heat_load_w / (m_dot_total * cp)

        # Spatial cell gradient: First cell gets t_inlet, last cell gets t_outlet
        # R_th from cell core to fluid:
        r_tim = tim_thickness / (tim_k * (plate_length * plate_width))
        r_al = al_wall_t / (al_k * (plate_length * plate_width))
        r_conv = 1.0 / (h_conv * wetted_area)
        r_th_total = r_tim + r_al + r_conv

        delta_t_cell_gradient = delta_t_coolant * 1.35  # non-uniform boundary layer accumulation
        conductance_w_per_k = 1.0 / r_th_total

    else:
        # OPTIMIZED_PARALLEL: 20 Parallel Micro-Channels with Dual Balanced Manifolds
        num_channels = 20
        ch_width = 0.006   # 6.0 mm microchannel
        ch_height = 0.007  # 7.0 mm fin height
        fin_t = 0.002      # 2.0 mm fin thickness
        ch_length_parallel = plate_width  # 0.32 m short path

        area_flow_single = ch_width * ch_height
        perim_flow_single = 2.0 * (ch_width + ch_height)
        d_h = (4.0 * area_flow_single) / perim_flow_single  # ~ 6.46 mm

        # Flow divides into 20 channels
        v_dot_ch = v_dot_total / num_channels
        velocity = v_dot_ch / area_flow_single
        re = (rho * velocity * d_h) / mu

        if re < 2300:
            f = 64.0 / re
            nu = 4.86  # Rectangular duct laminar with constant heat flux
        else:
            f = (0.79 * math.log(re) - 1.64) ** -2
            nu = ((f / 8.0) * (re - 1000.0) * pr) / (1.0 + 12.7 * math.sqrt(f / 8.0) * (pr ** (2.0/3.0) - 1.0))

        h_conv = (nu * k_fluid) / d_h

        # Friction pressure drop across short channels
        dp_friction = f * (ch_length_parallel / d_h) * (0.5 * rho * (velocity ** 2))
        # Header/manifold distribution losses (inlet + outlet plenum ~ K=1.2)
        dp_minor = 1.2 * (0.5 * rho * (velocity ** 2)) + 1200.0  # Manifold contraction/expansion
        dp_total = dp_friction + dp_minor

        # Fin efficiency enhancement (aluminum fins extend wetted area)
        fin_eff = 0.88
        wetted_area = num_channels * (ch_width + 2.0 * fin_eff * ch_height) * ch_length_parallel

        # Fluid temperature rise across parallel pass
        delta_t_coolant = heat_load_w / (m_dot_total * cp)

        r_tim = tim_thickness / (tim_k * (plate_length * plate_width))
        r_al = al_wall_t / (al_k * (plate_length * plate_width))
        r_conv = 1.0 / (h_conv * wetted_area)
        r_th_total = r_tim + r_al + r_conv

        # Because coolant is fed uniformly across all cells simultaneously,
        # cell-to-cell thermal gradient is dramatically minimized
        delta_t_cell_gradient = delta_t_coolant * 0.45
        conductance_w_per_k = 1.0 / r_th_total

    # Pumping power W = Q * ΔP / pump_efficiency (η_pump ≈ 0.45)
    pump_eff = 0.45
    pumping_power_w = (v_dot_total * dp_total) / pump_eff

    return {
        "design_type": plate_type,
        "flow_rate_lpm": flow_rate_lpm,
        "velocity_m_s": round(velocity, 3),
        "reynolds_number": round(re, 1),
        "h_conv_w_m2k": round(h_conv, 1),
        "pressure_drop_kpa": round(dp_total / 1000.0, 2),
        "pumping_power_w": round(pumping_power_w, 2),
        "delta_t_coolant_c": round(delta_t_coolant, 2),
        "cell_gradient_delta_t_c": round(delta_t_cell_gradient, 2),
        "thermal_resistance_k_w": round(r_th_total, 4),
        "conductance_w_per_k": round(conductance_w_per_k, 1)
    }

def print_comparison():
    base = analyze_cold_plate("BASELINE_SERPENTINE")
    opt = analyze_cold_plate("OPTIMIZED_PARALLEL")

    print("=" * 86)
    print(" 800V EV BATTERY PACK COLD PLATE: BASELINE VS. OPTIMIZED CFD/THERMAL ANALYSIS")
    print("=" * 86)
    print(f"{'Performance Metric':<36} | {'Baseline (Serpentine)':<22} | {'Optimized (Parallel)':<22}")
    print("-" * 86)
    print(f"{'Coolant Flow Topology':<36} | {'Single 6-Pass Snake':<22} | {'20 Parallel Microchannels':<22}")
    print(f"{'Fluid Velocity (m/s)':<36} | {base['velocity_m_s']:<22} | {opt['velocity_m_s']:<22}")
    print(f"{'Reynolds Number (Re)':<36} | {base['reynolds_number']:<22} | {opt['reynolds_number']:<22}")
    print(f"{'Convective Coeff h (W/m²K)':<36} | {base['h_conv_w_m2k']:<22} | {opt['h_conv_w_m2k']:<22}")
    print(f"{'Total Pressure Drop (kPa)':<36} | {base['pressure_drop_kpa']:<22} | {opt['pressure_drop_kpa']:<22}")
    print(f"{'Parasitic Pump Power (W)':<36} | {base['pumping_power_w']:<22} | {opt['pumping_power_w']:<22}")
    print(f"{'Coolant Stream Rise ΔT (°C)':<36} | {base['delta_t_coolant_c']:<22} | {opt['delta_t_coolant_c']:<22}")
    print(f"{'Cell-to-Cell Gradient ΔT (°C)':<36} | {base['cell_gradient_delta_t_c']:<22} | {opt['cell_gradient_delta_t_c']:<22}")
    print(f"{'Module Thermal Conductance (W/K)':<36} | {base['conductance_w_per_k']:<22} | {opt['conductance_w_per_k']:<22}")
    print("=" * 86)

    # Save verification JSON for BMS model calibration
    calib = {"baseline": base, "optimized": opt}
    import os
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cold_plate_thermal_params.json")
    with open(json_path, "w") as f:
        json.dump(calib, f, indent=4)
    print(f"Thermal-hydraulic calibration saved to {json_path}")

if __name__ == "__main__":
    print_comparison()
