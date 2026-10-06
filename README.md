[![ASIL-D SIL Verification Pipeline](https://github.com/naveen12005/ev-800v-bms-thermal-controller/actions/workflows/sil_pipeline.yml/badge.svg)](https://github.com/naveen12005/ev-800v-bms-thermal-controller/actions/workflows/sil_pipeline.yml)

# 800V High-Power EV BMS & Liquid Cold Plate Thermal Digital Twin

An advanced **Model-Based Systems Engineering (MBSE) Battery Digital Twin** modeling an 800V, 75 kWh liquid-cooled battery pack. Integrates parametric **CAD Cold Plate design (Baseline Serpentine vs. Optimized Parallel Microchannel)**, **2RC Thevenin Equivalent Circuit electrochemical kinetics**, **dual-node core/surface thermal physics**, and automated **ISO 26262 ASIL-D safety derating** with real-time **Lithium Plating boundary enforcement** under 350 kW DC ultra-fast charging.

---

## 1. System Architecture

```text
+----------------------------------------------------------------------------------------------------+
|                                    12S2P BATTERY MODULE ASSEMBLY                                   |
|   - 24x Prismatic Cells (148 x 27 x 91 mm, VDA / CATL standard format)                             |
|   - High-performance TIM Gap Pad (1.0 mm, k = 3.5 W/m.K)                                          |
|   - Aluminum Compression End Plates & Laser-welded Copper Busbars                                  |
+----------------------------------------------------------------------------------------------------+
                                                  |
                    +-----------------------------+-----------------------------+
                    |                                                           |
                    v                                                           v
+---------------------------------------+   +-------------------------------------------------------+
|  BASELINE: Serpentine Channel Plate   |   |        OPTIMIZED: Parallel Microchannel Plate         |
|  - 6-Pass Continuous Snake Loop       |   |  - Dual Balanced Manifolds (Inlet & Outlet Plenums)   |
|  - Channel: 14 mm W x 7 mm D          |   |  - 24 Parallel Microchannels (5.2 mm W x 8 mm D)      |
|  - Flow Length: 1.92 m                |   |  - Flow Length: 0.28 m (85% shorter path)             |
|  - High pressure drop, hot exit cells |   |  - High-aspect-ratio Aluminum Fins (1.8 mm thickness) |
+---------------------------------------+   +-------------------------------------------------------+
                    |                                                           |
                    +-----------------------------+-----------------------------+
                                                  v
+----------------------------------------------------------------------------------------------------+
|                             CLOSED-LOOP 800V BMS CONTROLLER (50ms LOOP)                            |
|   - Dual-Node Observer (T_core internal jelly roll vs. T_surf thermistor casing)                   |
|   - Proactive Thermal Actuator Control (PWM Coolant Pump 3-14 L/min + Chiller Solenoid)           |
|   - Lithium Plating Boundary Invariant (V_anode vs. Li/Li+ > 0.05V)                                |
|   - Continuous Model-Predictive Derating & Slew-Rate Limiter (<= 150 A/s)                          |
|   - ISO 14229 / UDS Diagnostic Trouble Codes (P0A7E, P0A80, P0B24)                                 |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Baseline vs. Optimized Cold Plate Performance

Evaluated for 50/50 Water-Ethylene Glycol (WEG) coolant under identical 350 kW DC fast-charging demand:

| Performance Metric | Baseline (Serpentine) | Optimized (Parallel Microchannel) | Automotive Impact |
| :--- | :--- | :--- | :--- |
| **Cooling Channel Topology** | Single 6-Pass Snake | 24 Parallel Microchannels | Balanced dual-manifold distribution |
| **Fluid Flow Path Length** | $1.92\text{ m}$ | $0.28\text{ m}$ | **85.4% shorter flow path** |
| **Hydraulic Pressure Drop ($\Delta P$)** | **$21.45\text{ kPa}$** | **$1.31\text{ kPa}$** | **93.9% reduction in hydraulic resistance** |
| **Coolant Pump Power** | **$18.5\text{ W / mod}$** | **$1.1\text{ W / mod}$** | **94.0% parasitic energy savings** |
| **Cell-to-Cell Gradient ($\Delta T_{spread}$)** | **$4.95^\circ\text{C}$** | **$1.56^\circ\text{C}$** | **Prevents asymmetric cell aging & capacity divergence** |
| **Module Thermal Conductance** | $70.3\text{ W/K}$ | $110.0\text{ W/K}$ | **56.5% higher heat dissipation** |
| **Fast-Charge Safety Mode** | Throttled by thermal gradients | Sustained 430 A fast charge | **Significantly reduces 10%–80% charge time** |

---

## 3. Parametric CAD Modeling & Siemens NX Integration

All CAD geometry is parametrically generated with direct bindings for **Siemens NX Open** and standalone 3D visualization:

* **Baseline Cold Plate:**
  * Generator: [`cad/baseline_serpentine_coldplate.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/baseline_serpentine_coldplate.py)
  * Siemens NX Journal: [`cad/nx_build_baseline_serpentine.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/nx_build_baseline_serpentine.py)
  * 3D STL Model: [`cad/baseline_serpentine_coldplate.stl`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/baseline_serpentine_coldplate.stl)
* **Optimized Microchannel Cold Plate:**
  * Generator: [`cad/optimized_microchannel_coldplate.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/optimized_microchannel_coldplate.py)
  * Siemens NX Journal: [`cad/nx_build_optimized_microchannel.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/nx_build_optimized_microchannel.py)
  * 3D STL Model: [`cad/optimized_microchannel_coldplate.stl`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/optimized_microchannel_coldplate.stl)
* **Full Module Assembly (Cells + TIM + Compression Plates + Cold Plate):**
  * Generator: [`cad/battery_module_12s2p.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/battery_module_12s2p.py)
  * 3D STL Model: [`cad/battery_module_12s2p_assembly.stl`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/battery_module_12s2p_assembly.stl)

---

## 4. Safety & Verification Invariants

The automated test suite ([`test_bms_derating.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/test_bms_derating.py)) enforces 8 formal safety requirements:
1. **ASIL-D Reaction Timing:** Derating command computed and issued within a 50ms control loop.
2. **Pack Overvoltage Invariant:** Pack voltage strictly limited to $\le 840.0\text{ V}$.
3. **Thermal Runaway Cutoff:** Hard 0A electrical contactor isolation at $T_{core} \ge 55.0^\circ\text{C}$ with DTC `P0A7E`.
4. **Inductive Transient Limit:** Current slew rate bounded to $\le 150\text{ A/s}$.
5. **DBC Matrix Fidelity:** Zero bit-drift serialization over SocketCAN (`bms_800v.dbc`).
6. **Lithium Plating Boundary Protection:** Immediate throttling and DTC `P0B24` emission if $V_{anode} < 0.05\text{ V}$.
7. **Proactive Actuator Response:** Automatic pump ramp to 14 L/min (100% duty) and chiller engagement before current derating.
8. **Spatial Gradient Verification:** Enforces module cell spread $\Delta T < 2.5^\circ\text{C}$ on optimized design.

---

## 5. Quick Start & Execution

```bash
# 1. Run Hydro-Thermal CFD Calculation & Calibration
python3 cad/thermal_fea_cfd_calc.py

# 2. Run Comparative 350kW Fast-Charge Simulation
python3 bms_controller.py

# 3. Run Automated Unit Test Suite
python3 -m unittest -v test_bms_derating.py
```

---

## 6. Academic References & Standards

1. **Gnielinski, V. (1976).** *"New equations for heat and mass transfer in turbulent pipe and channel flow."* *International Chemical Engineering*, 16(2), 359–368.
2. **Petukhov, B. S. (1970).** *"Heat transfer and friction in turbulent pipe flow with variable physical properties."* *Advances in Heat Transfer*, 6, 503–564.
3. **Shah, R. K., & London, A. L. (1978).** *Laminar Flow Forced Convection in Ducts.* Academic Press.
4. **Tuckerman, D. B., & Pease, R. F. (1981).** *"High-performance heat sinking for VLSI."* *IEEE Electron Device Letters*, 2(5), 126–129.
5. **Yang, X. G., Zhang, G., Ge, S., & Wang, C. Y. (2018).** *"Fast charging of lithium-ion batteries at all temperatures without lithium plating."* *Nature Energy*, 3(8), 674–686.
6. **Hu, X., Li, S., & Peng, H. (2012).** *"A comparative study of equivalent circuit models for Li-ion batteries."* *Journal of Power Sources*, 198, 359–367.
7. **ISO 26262-1:2018.** *Road Vehicles — Functional Safety.* ISO.
8. **ISO 14229-1:2020.** *Road Vehicles — Unified Diagnostic Services (UDS).* ISO.
