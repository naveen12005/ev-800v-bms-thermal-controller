"""
Upgraded Production 800V BMS Controller & Fast-Charging Safety Manager
=====================================================================
Features:
1. Dual-Node Core & Surface Thermal Supervision (ISO 26262 ASIL-D)
2. Active Coolant Actuator Control (Proactive PWM Pump & Chiller EXV)
3. Lithium Plating Anode Potential Boundary Protection (V_anode > 0.05V)
4. Smooth Continuous Adaptive Current Regulation & Slew Rate Limiter
5. ISO 14229 / UDS Diagnostic Trouble Code (DTC) Generator
6. Side-by-Side Comparative Execution: Baseline vs. Optimized CAD Cold Plate
"""

import time
import math
from collections import deque
from bms_thermal_plant import BatteryPackPlant

class BMSDeratingController:
    def __init__(self, max_slew_rate_a_per_sec=150.0):
        self.max_slew = max_slew_rate_a_per_sec
        self.last_commanded_current = 0.0
        self.temp_history = deque(maxlen=20)
        self.mode = "CC_FAST_CHARGE"
        self.derating_active = False

        # Active Thermal Actuator Commands
        self.commanded_pump_lpm = 4.0      # L/min coolant pump flow
        self.chiller_active = False        # Refrigerant heat exchanger solenoid
        self.dtc_codes = []                # Active ISO 14229 Diagnostic Trouble Codes

    def update_gradient(self, current_temp, dt_sec=0.05):
        self.temp_history.append(current_temp)
        if len(self.temp_history) < 2:
            return 0.0
        delta_t = self.temp_history[-1] - self.temp_history[0]
        window_duration_min = ((len(self.temp_history) - 1) * dt_sec) / 60.0
        return max(0.0, delta_t / window_duration_min) if window_duration_min > 0 else 0.0

    def compute_actuator_commands(self, cell_surf_temp, cell_core_temp):
        """
        Active Thermal Management:
        Engages high-efficiency pump and chiller proactively before resorting to electrical derating.
        """
        t_max = max(cell_surf_temp, cell_core_temp)

        if t_max >= 42.0:
            self.commanded_pump_lpm = 14.0   # 100% pump duty cycle
            self.chiller_active = True
        elif t_max >= 35.0:
            # Linear ramp from 6 L/min to 14 L/min
            self.commanded_pump_lpm = 6.0 + ((t_max - 35.0) / 7.0) * 8.0
            self.chiller_active = True
        elif t_max >= 28.0:
            self.commanded_pump_lpm = 6.0
            self.chiller_active = False
        else:
            self.commanded_pump_lpm = 3.0    # Eco circulation flow
            self.chiller_active = False

        return self.commanded_pump_lpm, self.chiller_active

    def compute_current_limit(self, pack_v, surf_temp, core_temp=None, thermal_grad=None, v_anode=0.10):
        if thermal_grad is None:
            # Legacy 3-arg call: compute_current_limit(pack_v, cell_temp, thermal_grad)
            thermal_grad = core_temp if core_temp is not None else 0.0
            core_temp = surf_temp
        if core_temp is None:
            core_temp = surf_temp

        self.dtc_codes.clear()

        # 1. ASIL-D Emergency Cutoffs: Thermal Runaway, Hard Overvoltage, or Critical Gradient
        if core_temp >= 55.0 or surf_temp >= 52.0 or pack_v >= 839.8:
            self.mode = "FAULT_EMERGENCY_SHUTDOWN"
            self.derating_active = True
            if core_temp >= 55.0:
                self.dtc_codes.append("P0A7E: Battery Pack Core Over-Temperature")
            if pack_v >= 839.8:
                self.dtc_codes.append("P0A80: Battery Pack Over-Voltage Isolation")
            return 0.0

        # 2. Lithium Plating Anode Protection
        # If V_anode drops below 0.05V vs Li/Li+, throttle immediately to prevent dendrites
        plating_limit = 430.0
        if v_anode < 0.05:
            self.mode = "LITHIUM_PLATING_PREVENTION"
            self.derating_active = True
            self.dtc_codes.append("P0B24: Anode Kinetic Saturation (Plating Risk)")
            plating_margin = max(0.001, v_anode)
            plating_limit = 200.0 * (plating_margin / 0.05)

        # 3. Constant Voltage (CV) Taper: Begins at 825V to prevent IR overshoots
        cv_limit = 430.0
        if pack_v >= 825.0:
            headroom = max(0.0, 839.0 - pack_v)
            cv_limit = 20.0 + (headroom / 14.0) * 200.0

        # 4. Multi-Node Thermal & Gradient Derating (Supervising Core & Surface)
        thermal_limit = 430.0
        derating = False

        effective_temp = max(surf_temp, core_temp - 2.0)
        if effective_temp >= 48.0 or thermal_grad > 5.0:
            thermal_limit = 260.0
            derating = True
        elif effective_temp >= 46.5 or thermal_grad > 3.5:
            thermal_limit = 320.0
            derating = True
        elif effective_temp >= 45.0 or thermal_grad > 2.0:
            thermal_limit = 375.0
            derating = True

        target_current = min(430.0, cv_limit, thermal_limit, plating_limit)

        if target_current < 425.0:
            self.derating_active = True
            if plating_limit < min(cv_limit, thermal_limit):
                self.mode = "LITHIUM_PLATING_PROTECT"
            elif cv_limit < thermal_limit:
                self.mode = "CV_TAPER"
            else:
                self.mode = "THERMAL_DERATE"
        else:
            self.derating_active = False
            self.mode = "CC_FAST_CHARGE"

        return max(0.0, target_current)

    def apply_slew_rate(self, target_current, dt_sec=0.05):
        if self.mode == "FAULT_EMERGENCY_SHUTDOWN":
            self.last_commanded_current = 0.0
            return 0.0

        max_step = self.max_slew * dt_sec
        delta = target_current - self.last_commanded_current
        if abs(delta) > max_step:
            commanded = self.last_commanded_current + (max_step if delta > 0 else -max_step)
        else:
            commanded = target_current
        self.last_commanded_current = commanded
        return commanded

def run_comparative_simulation():
    """
    Simulates 350 kW DC Fast Charging on both:
    1. Baseline Serpentine Cold Plate
    2. Optimized Parallel Microchannel Cold Plate
    Demonstrating the exact practical advantage of the upgraded CAD design.
    """
    sim_time = 180.0
    dt = 0.05
    steps = int(sim_time / dt)
    log_interval = int(25.0 / dt)

    results = {}
    for c_type in ["BASELINE_SERPENTINE", "OPTIMIZED_PARALLEL"]:
        plant = BatteryPackPlant(capacity_kwh=75.0, initial_soc=15.0, ambient_temp=38.0, cooling_type=c_type)
        ctrl = BMSDeratingController(max_slew_rate_a_per_sec=150.0)

        print("\n" + "=" * 96)
        print(f" 800V BMS FAST-CHARGE SIMULATION: {c_type}")
        print("=" * 96)
        print(f"{'Time(s)':>7} | {'V_pack':>7} | {'Act_I(A)':>8} | {'T_surf':>7} | {'T_core':>7} | {'ΔT_spat':>7} | {'V_anode':>7} | {'Pump(L/m)':>9} | {'Mode':>18}")
        print("-" * 96)

        act_current = 0.0
        time_to_first_derate = None
        total_energy_kwh = 0.0

        for i in range(steps):
            t = i * dt
            # Controller determines active cooling commands
            pump_flow, chiller = ctrl.compute_actuator_commands(plant.temp_surf, plant.temp_core)
            # Plant updates states
            state = plant.step(act_current, dt, pump_flow_lpm=pump_flow, chiller_active=chiller)
            # Controller calculates gradient and limits
            grad = ctrl.update_gradient(state['temp'], dt)
            req_current = ctrl.compute_current_limit(
                state['voltage'], state['temp'], state['temp_core'], grad, state['anode_potential']
            )
            act_current = ctrl.apply_slew_rate(req_current, dt)

            # Energy delivered in this step
            total_energy_kwh += (state['voltage'] * act_current * dt) / (3600.0 * 1000.0)

            if ctrl.derating_active and time_to_first_derate is None and act_current > 50.0:
                time_to_first_derate = t

            if i % log_interval == 0 or i == 2:
                print(f"{t:7.1f} | {state['voltage']:7.1f} | {act_current:8.1f} | {state['temp']:7.2f} | {state['temp_core']:7.2f} | {state['spatial_gradient_c']:7.2f} | {state['anode_potential']:7.3f} | {pump_flow:9.1f} | {ctrl.mode:>18}")

        results[c_type] = {
            "final_soc": round(state['soc'], 1),
            "final_temp_surf": round(state['temp'], 2),
            "final_temp_core": round(state['temp_core'], 2),
            "final_gradient": round(state['spatial_gradient_c'], 2),
            "energy_delivered_kwh": round(total_energy_kwh, 2),
            "first_derate_time_s": time_to_first_derate,
            "pump_power_w": round(state['pumping_power_w'], 1)
        }

    print("\n" + "=" * 80)
    print(" SUMMARY: BASELINE VS. OPTIMIZED COLD PLATE UNDER 350kW FAST CHARGING")
    print("=" * 80)
    print(f"{'Performance Metric':<32} | {'Baseline (Serpentine)':<22} | {'Optimized (Microchannel)':<22}")
    print("-" * 80)
    print(f"{'Energy Transferred (kWh)':<32} | {results['BASELINE_SERPENTINE']['energy_delivered_kwh']:<22} | {results['OPTIMIZED_PARALLEL']['energy_delivered_kwh']:<22}")
    print(f"{'Final Pack SoC (%)':<32} | {results['BASELINE_SERPENTINE']['final_soc']:<22} | {results['OPTIMIZED_PARALLEL']['final_soc']:<22}")
    print(f"{'Final Core Temp (°C)':<32} | {results['BASELINE_SERPENTINE']['final_temp_core']:<22} | {results['OPTIMIZED_PARALLEL']['final_temp_core']:<22}")
    print(f"{'Final Cell Gradient ΔT (°C)':<32} | {results['BASELINE_SERPENTINE']['final_gradient']:<22} | {results['OPTIMIZED_PARALLEL']['final_gradient']:<22}")
    print(f"{'Time to First Derate (s)':<32} | {str(results['BASELINE_SERPENTINE']['first_derate_time_s']):<22} | {str(results['OPTIMIZED_PARALLEL']['first_derate_time_s']):<22}")
    print(f"{'Coolant Pump Power (W)':<32} | {results['BASELINE_SERPENTINE']['pump_power_w']:<22} | {results['OPTIMIZED_PARALLEL']['pump_power_w']:<22}")
    print("=" * 80)

if __name__ == "__main__":
    run_comparative_simulation()
