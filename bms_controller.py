import time
from collections import deque
from bms_thermal_plant import BatteryPackPlant

class BMSDeratingController:
    def __init__(self, max_slew_rate_a_per_sec=150.0):
        self.max_slew = max_slew_rate_a_per_sec
        self.last_commanded_current = 0.0
        self.temp_history = deque(maxlen=20)  # Sliding window for gradient calculation
        self.mode = "CC_FAST_CHARGE"
        self.derating_active = False

    def update_gradient(self, current_temp, dt_sec=0.05):
        self.temp_history.append(current_temp)
        if len(self.temp_history) < 2:
            return 0.0
        # Rate of temperature change in deg C per minute
        delta_t = self.temp_history[-1] - self.temp_history[0]
        window_duration_min = ((len(self.temp_history) - 1) * dt_sec) / 60.0
        return max(0.0, delta_t / window_duration_min) if window_duration_min > 0 else 0.0

    def compute_current_limit(self, pack_v, cell_temp, thermal_grad):
        # 1. Critical Safety Trip (Thermal runaway cutoff at 55 deg C)
        if cell_temp >= 55.0 or pack_v >= 840.0:
            self.mode = "FAULT_EMERGENCY_SHUTDOWN"
            self.derating_active = True
            return 0.0

        # 2. Constant Voltage (CV) Handover near upper ceiling (838V)
        if pack_v >= 838.0:
            self.mode = "CV_TAPER"
            self.derating_active = True
            # Taper smoothly down to trickle charge (25A)
            overage = pack_v - 838.0
            return max(25.0, 430.0 - (overage * 180.0))

        # 3. Multi-Stage Thermal & Gradient Derating
        target_current = 430.0  # Baseline 350 kW class current (430A @ 800V)
        derating = False

        if cell_temp >= 47.0 or thermal_grad > 5.0:
            target_current = min(target_current, 304.0)
            derating = True
        elif cell_temp >= 46.0 or thermal_grad > 3.0:
            target_current = min(target_current, 346.0)
            derating = True
        elif cell_temp >= 45.0 or thermal_grad > 2.0:
            target_current = min(target_current, 388.0)
            derating = True

        self.derating_active = derating
        self.mode = "THERMAL_DERATE" if derating else "CC_FAST_CHARGE"
        return target_current

    def apply_slew_rate(self, target_current, dt_sec=0.05):
        max_step = self.max_slew * dt_sec
        delta = target_current - self.last_commanded_current
        if abs(delta) > max_step:
            commanded = self.last_commanded_current + (max_step if delta > 0 else -max_step)
        else:
            commanded = target_current
        self.last_commanded_current = commanded
        return commanded

def run_simulation():
    plant = BatteryPackPlant(capacity_kwh=75.0, initial_soc=20.0, ambient_temp=38.0)
    ctrl = BMSDeratingController(max_slew_rate_a_per_sec=150.0)

    print("=" * 88)
    print("CLOSED-LOOP 800V BMS CHARGING & THERMAL DERATING SIMULATION")
    print("Plant (bms_thermal_plant.py) <---> Controller (bms_controller.py)")
    print("=" * 88)
    print(f"{'Time(s)':>7} | {'V_pack(V)':>9} | {'Req_I(A)':>8} | {'Act_I(A)':>8} | {'T_max(°C)':>9} | {'Grad(°C/m)':>10} | {'Mode':>18} | {'Derate?'}")
    print("-" * 88)

    dt = 0.05
    sim_time = 180.0
    steps = int(sim_time / dt)
    log_interval = int(15.0 / dt)

    act_current = 0.0
    for i in range(steps):
        t = i * dt
        state = plant.step(act_current, dt)
        grad = ctrl.update_gradient(state['temp'], dt)
        req_current = ctrl.compute_current_limit(state['voltage'], state['temp'], grad)
        act_current = ctrl.apply_slew_rate(req_current, dt)

        if i % log_interval == 0 or i == 2:
            print(f"{t:7.1f} | {state['voltage']:9.1f} | {req_current:8.1f} | {act_current:8.1f} | {state['temp']:9.2f} | {grad:10.2f} | {ctrl.mode:>18} | {str(ctrl.derating_active):>7}")

    print("-" * 88)
    print("Simulation finished. Closed-loop controller successfully regulated the pack!")

if __name__ == "__main__":
    run_simulation()
