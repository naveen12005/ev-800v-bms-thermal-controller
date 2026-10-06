# 800V EV BMS & Liquid Cold Plate Thermal Digital Twin: Baseline vs. Optimized Engineering Report

**Project:** 800V / 75 kWh Electric Vehicle Battery Management System  
**Subsystem:** Battery Thermal Management System (BTMS) & ISO 26262 ASIL-D Derating Controller  
**Author:** Rathlavath Naveen  
**Repository:** `ev-800v-bms-thermal-controller`  

---

## 1. Executive Summary & Problem Statement

Under **350 kW DC Extreme Fast Charging (XFC)** (peak current $\sim 430\text{ A}$ into an 800V, 75 kWh pack), lithium-ion battery packs encounter severe thermodynamic and electrochemical bottlenecks:
1. **Massive Heat Generation:** Up to $11\text{--}14\text{ kW}$ of Joule ($I^2 R$) and entropic heat is generated across the pack.
2. **Internal Thermal Gradient:** Due to low transverse thermal conductivity ($k_{radial} \approx 0.8\text{--}1.2\text{ W/m}\cdot\text{K}$), the core jelly roll temperature ($T_{core}$) runs $6\text{--}10^\circ\text{C}$ hotter than the outer casing ($T_{surf}$).
3. **Lithium Plating Risk:** High charge C-rates drive negative electrode potentials below 0V vs $\text{Li/Li}^+$, triggering irreversible metallic lithium dendrite formation.
4. **Hydraulic vs. Thermal Trade-Off:** Traditional serpentine cooling plates exhibit long flow paths, high pressure drops ($\Delta P$), and severe cell-to-cell temperature gradients ($\Delta T > 5^\circ\text{C}$).

This project implements an **end-to-end electro-thermal digital twin** integrating:
* **Parametric CAD Modeling** (Baseline Serpentine vs. Optimized Parallel Microchannel with Siemens NX Open journals)
* **Analytical Fluid & Heat Transfer Calculations** ($Re, Nu, h, \Delta P, W_{pump}$)
* **2RC Thevenin Electrochemical Equivalent Circuit Model (ECM)**
* **Dual-State Thermal Plant Model** ($T_{core}$ vs. $T_{surf}$)
* **Production-Grade BMS Controller** with proactive pump/chiller modulation, lithium plating boundary enforcement, and ISO 14229 / UDS diagnostics.

---

## 2. Cold Plate CAD Architecture Comparison

```
+----------------------------------------------------------------------------------------------------+
|                                    12S2P BATTERY MODULE ASSEMBLY                                   |
|   - 24x Prismatic Cells (148 x 27 x 91 mm)                                                         |
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
|  - Long single-tube residence time    |   |  - High-aspect-ratio Aluminum Fins (1.8 mm thickness) |
+---------------------------------------+   +-------------------------------------------------------+
```

### CAD Artifacts Generated
* **Baseline CAD:**
  * Script: `cad/baseline_serpentine_coldplate.py`
  * Siemens NX Open Journal: `cad/nx_build_baseline_serpentine.py`
  * 3D Facet Mesh: `cad/baseline_serpentine_coldplate.stl`
* **Optimized CAD:**
  * Script: `cad/optimized_microchannel_coldplate.py`
  * Siemens NX Open Journal: `cad/nx_build_optimized_microchannel.py`
  * 3D Facet Mesh: `cad/optimized_microchannel_coldplate.stl`
* **Full Module Assembly:**
  * Script: `cad/battery_module_12s2p.py`
  * 3D Facet Mesh: `cad/battery_module_12s2p_assembly.stl`

---

## 3. Hydro-Thermal & CFD Performance Comparison

Evaluated for 50/50 Water-Ethylene Glycol (WEG) coolant at $8.0\text{ L/min}$ flow rate:

| Metric | Baseline (Serpentine) | Optimized (Parallel Microchannel) | Improvement / Impact |
| :--- | :--- | :--- | :--- |
| **Cooling Channel Topology** | Single 6-Pass Snake | 24 Parallel Microchannels | Balanced manifold feed |
| **Coolant Flow Path Length** | $1.92\text{ m}$ | $0.28\text{ m}$ | **85.4% shorter path** |
| **Fluid Channel Velocity** | $1.59\text{ m/s}$ | $0.16\text{ m/s}$ | Low velocity laminar flow |
| **Hydraulic Pressure Drop ($\Delta P$)** | **$21.45\text{ kPa}$** | **$1.31\text{ kPa}$** | **93.9% reduction in pressure drop** |
| **Module Parasitic Pump Power** | **$6.36\text{ W}$** | **$0.39\text{ W}$** | **93.9% parasitic energy savings** |
| **Cell-to-Cell Thermal Spread ($\Delta T_{spread}$)** | **$4.95^\circ\text{C}$** | **$1.56^\circ\text{C}$** | **68.5% improvement in thermal uniformity** |
| **Module Thermal Conductance** | $70.3\text{ W/K}$ | $110.0\text{ W/K}$ | **56.5% higher heat dissipation** |

---

## 4. Closed-Loop Fast-Charging Simulation Results (350 kW DC Demand)

Tested over a 180-second continuous 430 A fast-charge burst:

```text
================================================================================
 SUMMARY: BASELINE VS. OPTIMIZED COLD PLATE UNDER 350kW FAST CHARGING
================================================================================
Performance Metric               | Baseline (Serpentine)  | Optimized (Microchannel)
--------------------------------------------------------------------------------
Energy Transferred (kWh)         | 10.01                  | 10.04
Final Pack SoC (%)               | 30.3                   | 30.4
Final Core Temp (°C)             | 40.00                  | 40.51
Final Cell Gradient ΔT (°C)      | 4.95                   | 1.56  <-- PASS (<2.5°C)
Time to First Derate (s)         | 2.05                   | 2.05
Coolant Pump Power (W)           | 18.5 W                 | 1.1 W <-- 94% REDUCTION
================================================================================
```

### Key Engineering Insights
1. **Cell Degradation Mitigation:** The baseline serpentine cold plate produces a cell-to-cell temperature spread of nearly $5.0^\circ\text{C}$. In an EV pack, a $5^\circ\text{C}$ permanent gradient causes cells near the outlet to degrade twice as fast as cells near the inlet, triggering premature pack replacement. The optimized design caps the gradient at $1.56^\circ\text{C}$.
2. **Pumping Power Savings:** Reducing cold plate pressure drop drops total pack auxiliary pumping power from $\sim 300\text{ W}$ down to under $20\text{ W}$, directly improving EV driving range.
3. **Electrochemical Safety:** The controller's real-time $V_{anode}$ observer successfully prevents lithium plating by limiting current when overpotential margins shrink below $0.05\text{ V}$.

---

## 5. How to Run & Verify

### 1. Run Hydro-Thermal Verification
```bash
python3 cad/thermal_fea_cfd_calc.py
```

### 2. Generate Parametric 3D CAD Models (STL & Siemens NX Open Journals)
```bash
python3 cad/baseline_serpentine_coldplate.py
python3 cad/optimized_microchannel_coldplate.py
python3 cad/battery_module_12s2p.py
```

### 3. Run Closed-Loop 800V BMS Comparative Simulation
```bash
python3 bms_controller.py
```

### 4. Execute Automated Verification Suite
```bash
python3 -m unittest -v test_bms_derating.py
```
