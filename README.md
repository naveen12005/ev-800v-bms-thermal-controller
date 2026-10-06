[![ASIL-D SIL Verification Pipeline](https://github.com/naveen12005/ev-800v-bms-thermal-controller/actions/workflows/sil_pipeline.yml/badge.svg)](https://github.com/naveen12005/ev-800v-bms-thermal-controller/actions/workflows/sil_pipeline.yml)

# 800V High-Power EV BMS & Liquid Cold Plate Thermal Digital Twin

An advanced **Model-Based Systems Engineering (MBSE) Battery Digital Twin** modeling an 800V, 75 kWh liquid-cooled battery pack. Integrates parametric **CAD Cold Plate design (Baseline Serpentine vs. Optimized Parallel Microchannel)**, **2RC Thevenin Equivalent Circuit electrochemical kinetics**, **dual-node core/surface thermal physics**, and automated **ISO 26262 ASIL-D safety derating** with real-time **Lithium Plating boundary enforcement** under 350 kW DC ultra-fast charging.

---

## 1. Industry-Grade Problems vs. Engineering Solutions

| # | Automotive Industry Problem (800V / 350 kW XFC) | Root Cause & Failure Mechanism | Implemented Solution in this Digital Twin | Verification & Evidence |
| :- | :--- | :--- | :--- | :--- |
| **1** | **Severe Cell-to-Cell Thermal Gradient ($\Delta T > 5^\circ\text{C}$)** | Long single-pass serpentine channels heat up coolant sequentially, subjecting downstream cells to high coolant temperatures, accelerating cell aging divergence. | **Dual-manifold balanced parallel microchannel cold plate (24 channels)** feeding identical fresh coolant across all cells simultaneously. | Cell spread reduced by **68.5%** ($4.95^\circ\text{C} \rightarrow 1.56^\circ\text{C}$), meeting strict OEM warranty targets ($< 2.0^\circ\text{C}$). |
| **2** | **Excessive Hydraulic Pumping Parasitic Loss ($\Delta P > 20\text{ kPa}$)** | Long fluid flow path ($1.92\text{ m}$) with 180° return bends causing high Darcy friction and minor pressure losses ($> 20\text{ kPa}$), draining EV battery range via pump power. | **Short-path microchannel architecture ($0.28\text{ m}$)** reducing fluid path length by **85.4%** and optimizing hydraulic diameter ($D_h = 6.30\text{ mm}$). | Hydraulic pressure drop reduced by **93.9%** ($21.45\text{ kPa} \rightarrow 1.31\text{ kPa}$); pump parasitic power cut by **94.0%** ($18.5\text{ W} \rightarrow 1.1\text{ W/mod}$). |
| **3** | **Sub-Surface Metallic Lithium Plating & Dendrite Shorting** | Fast charging at low temperatures or high C-rates pushes negative electrode potential below 0V vs $\text{Li/Li}^+$ ($V_{anode} < 0\text{V}$), depositing metallic lithium and risking thermal runaway. | **Electrochemical-coupled 2RC Thevenin ECM with real-time $V_{anode}$ observer** and closed-loop continuous model-predictive current throttling ($V_{anode} \ge 0.05\text{V}$). | Sustained safe 350 kW charging without lithium plating; automated ISO 14229 UDS DTC `P0B24` emitted if boundary is approached. |
| **4** | **Core vs. Surface Thermal Measurement Lag** | External NTC surface thermistors lag internal jelly-roll core temperature by 10–15°C during 430A charge pulses, causing delayed BMS protection. | **Dual-Node Thermal Observer ($T_{core}$ vs $T_{surf}$)** capturing internal-to-case conduction resistance and proactive actuator feedforward (pump + chiller). | Contactor emergency cutoff guaranteed at $T_{core} \ge 55^\circ\text{C}$ ($< 50\text{ ms}$ reaction time, ISO 26262 ASIL-D compliant). |

---

## 2. System Architecture

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
|  - Flow Length: 1.92 m                |   |  - Flow Length: 0.28 m (85.4% shorter path)           |
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

## 3. Baseline vs. Optimized Cold Plate Performance

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

## 4. Parametric CAD Modeling & Siemens NX Integration

All CAD solids are provided in **ISO 10303-21 STEP (`.step` / `.stp`)** format for direct compatibility with **Siemens NX Design Center (including Student Edition)**, along with parametric Python generators and STL meshes:

* **Baseline Cold Plate (Serpentine):**
  * STEP Models: [`cad/baseline_serpentine_coldplate.step`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/baseline_serpentine_coldplate.step) & [`cad/baseline_serpentine_coldplate.stp`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/baseline_serpentine_coldplate.stp)
  * Generator: [`cad/baseline_serpentine_coldplate.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/baseline_serpentine_coldplate.py)
  * Siemens NX Journal: [`cad/nx_build_baseline_serpentine.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/nx_build_baseline_serpentine.py)
  * 3D STL Model: [`cad/baseline_serpentine_coldplate.stl`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/baseline_serpentine_coldplate.stl)

* **Optimized Cold Plate (Parallel Microchannel):**
  * STEP Models: [`cad/optimized_microchannel_coldplate.step`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/optimized_microchannel_coldplate.step) & [`cad/optimized_microchannel_coldplate.stp`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/optimized_microchannel_coldplate.stp)
  * Generator: [`cad/optimized_microchannel_coldplate.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/optimized_microchannel_coldplate.py)
  * Siemens NX Journal: [`cad/nx_build_optimized_microchannel.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/nx_build_optimized_microchannel.py)
  * 3D STL Model: [`cad/optimized_microchannel_coldplate.stl`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/optimized_microchannel_coldplate.stl)

* **Full 12S2P Battery Module Assembly:**
  * STEP Models: [`cad/battery_module_12s2p_assembly.step`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/battery_module_12s2p_assembly.step) & [`cad/battery_module_12s2p_assembly.stp`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/battery_module_12s2p_assembly.stp)
  * Generator: [`cad/battery_module_12s2p.py`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/battery_module_12s2p.py)
  * 3D STL Model: [`cad/battery_module_12s2p_assembly.stl`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/cad/battery_module_12s2p_assembly.stl)

---

## 5. CFD Hydro-Thermal Analysis & Engineering Documents

Detailed mathematical derivations, FEA/CFD calculations, and comparative plots are published in the project documents:
* **Microsoft Word Comparison Report:** [`reports/800V_BMS_ColdPlate_Upgrade_and_Solution_Comparison.docx`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/reports/800V_BMS_ColdPlate_Upgrade_and_Solution_Comparison.docx)
* **Markdown Executive Comparison Report:** [`reports/EXECUTIVE_UPGRADE_AND_SOLUTION_COMPARISON.md`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/reports/EXECUTIVE_UPGRADE_AND_SOLUTION_COMPARISON.md)
* **High-Resolution Figures:**
  * Pressure Drop vs. Flow Rate: [`reports/figures/cfd_pressure_drop_comparison.png`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/reports/figures/cfd_pressure_drop_comparison.png)
  * Spatial Cell Temperature Distribution: [`reports/figures/cfd_spatial_temperature_distribution.png`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/reports/figures/cfd_spatial_temperature_distribution.png)
  * Transient Fast-Charge Response: [`reports/figures/cfd_transient_thermal_fastcharge.png`](file:///c:/NaveenCADAgent/ev-800v-bms-thermal-controller/reports/figures/cfd_transient_thermal_fastcharge.png)

---

## 6. Safety & Verification Invariants

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

## 7. Quick Start & Execution

```bash
# 1. Run Hydro-Thermal CFD Calculation & Calibration
python3 cad/thermal_fea_cfd_calc.py

# 2. Run Comparative 350kW Fast-Charge Simulation
python3 bms_controller.py

# 3. Run Automated Unit Test Suite
python3 -m unittest -v test_bms_derating.py
```

---

## 8. Academic References & Engineering Standards

The models and mathematical equations in this repository are rigorously grounded in established literature and automotive standards:

### Convective Heat Transfer & Microchannel Fluid Dynamics
1. **Gnielinski, V. (1976).** *"New equations for heat and mass transfer in turbulent pipe and channel flow."* *International Chemical Engineering*, 16(2), 359–368.  
   *(Provides the transitional & turbulent Nusselt number correlation used to determine convective heat transfer coefficients $h$ in cooling passages).*
2. **Petukhov, B. S. (1970).** *"Heat transfer and friction in turbulent pipe flow with variable physical properties."* *Advances in Heat Transfer*, 6, 503–564.  
   *(Provides the turbulent Darcy friction factor formula $f = (0.790 \ln \text{Re} - 1.64)^{-2}$ governing hydraulic pressure drop).*
3. **Shah, R. K., & London, A. L. (1978).** *Laminar Flow Forced Convection in Ducts.* Academic Press.  
   *(Defines laminar aspect-ratio-dependent Nusselt number asymptotic limits for rectangular microchannels).*
4. **Tuckerman, D. B., & Pease, R. F. (1981).** *"High-performance heat sinking for VLSI."* *IEEE Electron Device Letters*, 2(5), 126–129.  
   *(Foundational theory establishing parallel microchannel heat sinks for ultra-low thermal resistance under high heat flux).*

### Electrochemical Kinetics & Degradation Physics
5. **Yang, X. G., Zhang, G., Ge, S., & Wang, C. Y. (2018).** *"Fast charging of lithium-ion batteries at all temperatures without lithium plating."* *Nature Energy*, 3(8), 674–686.  
   *(Defines the critical negative electrode overpotential threshold $V_{anode} > 0\text{V}$ vs $\text{Li/Li}^+$ to prevent irreversible metallic lithium deposition).*
6. **Arora, P., Doyle, M., & Newman, J. (1999).** *"Mathematical modeling of the lithium deposition overcharge reaction of lithium-ion batteries."* *Journal of the Electrochemical Society*, 146(10), 3543–3553.  
   *(Establishes Butler-Volmer kinetics for lithium insertion vs. parasitic metallic lithium plating).*
7. **Hu, X., Li, S., & Peng, H. (2012).** *"A comparative study of equivalent circuit models for Li-ion batteries."* *Journal of Power Sources*, 198, 359–367.  
   *(Provides formulation and parameter identification methods for the 2RC Thevenin Equivalent Circuit Model).*

### Automotive & Functional Safety Standards
8. **ISO 26262-1:2018.** *Road Vehicles — Functional Safety.* ISO. *(ASIL-D reaction time constraints, dual-node core temperature safety invariants, and contactor isolation).*
9. **ISO 14229-1:2020.** *Road Vehicles — Unified Diagnostic Services (UDS).* ISO. *(Diagnostic trouble code emission: P0A7E, P0A80, P0B24).*
10. **SAE J1939 / ISO 11898.** *Controller Area Network (CAN) Protocol Framework.* SAE International. *(DBC signal packing and CAN arbitration).*
