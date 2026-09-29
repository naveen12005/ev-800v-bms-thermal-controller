import unittest
import cantools
from bms_thermal_plant import BatteryPackPlant
from bms_controller import BMSDeratingController

class TestBMSDeratingSafetyPipeline(unittest.TestCase):
    def setUp(self):
        self.plant = BatteryPackPlant(capacity_kwh=75.0, initial_soc=20.0, ambient_temp=38.0)
        self.ctrl = BMSDeratingController(max_slew_rate_a_per_sec=150.0)
        self.db = cantools.database.load_file("bms_800v.dbc")

    def test_01_derating_reaction_time_within_50ms(self):
        """ISO 26262 ASIL-D Timing Requirement: Current derate command within 50ms of thermal threshold."""
        self.plant.temp_c = 45.1
        grad = self.ctrl.update_gradient(self.plant.temp_c, dt_sec=0.05)
        req_current = self.ctrl.compute_current_limit(self.plant.pack_voltage, self.plant.temp_c, grad)
        
        self.assertTrue(self.ctrl.derating_active, "Derating flag must be active at 45.1 C")
        self.assertLess(req_current, 430.0, "Current request must drop below maximum 430A")

    def test_02_pack_voltage_never_exceeds_840v(self):
        """ASIL-D Overvoltage Invariant: Pack voltage must not exceed 840.0V under continuous charging."""
        self.plant.soc = 98.0
        # Initialize loop from current plant state
        for _ in range(200):
            grad = self.ctrl.update_gradient(self.plant.temp_c, dt_sec=0.05)
            req = self.ctrl.compute_current_limit(self.plant.pack_voltage, self.plant.temp_c, grad)
            act_current = self.ctrl.apply_slew_rate(req, dt_sec=0.05)
            state = self.plant.step(act_current, dt_sec=0.05)
            
            self.assertLessEqual(state['voltage'], 840.0, f"Overvoltage detected: {state['voltage']}V")

    def test_03_thermal_runaway_trip_at_55c(self):
        """ASIL-D Critical Emergency Cutoff: Immediate 0A shutdown upon hitting 55 deg C."""
        self.plant.temp_c = 55.0
        req = self.ctrl.compute_current_limit(750.0, self.plant.temp_c, 1.0)
        self.assertEqual(req, 0.0, "Controller must demand 0A immediately upon hitting 55 C")
        self.assertEqual(self.ctrl.mode, "FAULT_EMERGENCY_SHUTDOWN")

    def test_04_slew_rate_limiter_bounds(self):
        """Hardware Protection: di/dt must stay within 150 A/s to mitigate inductive voltage spikes."""
        dt = 0.05
        max_allowed_delta = 150.0 * dt  # 7.5 A per step
        self.ctrl.last_commanded_current = 430.0
        target_emergency_stop = 0.0
        
        slew_limited = self.ctrl.apply_slew_rate(target_emergency_stop, dt_sec=dt)
        actual_delta = abs(430.0 - slew_limited)
        self.assertAlmostEqual(actual_delta, max_allowed_delta, places=2)

    def test_05_can_matrix_serialization_fidelity(self):
        """DBC Protocol Verification: Ensure pack metrics pack/unpack without bit corruption."""
        msg = self.db.get_message_by_name("BMS_PackMetrics")
        encoded = msg.encode({
            'PackVoltage': 800.5,
            'PackCurrent': 415.2,
            'StateOfCharge': 75.5,
            'MaxCellTemp': 44.0,
            'DeratingActive': 1
        })
        decoded = msg.decode(encoded)
        self.assertAlmostEqual(decoded['PackVoltage'], 800.5, delta=0.1)
        self.assertAlmostEqual(decoded['PackCurrent'], 415.2, delta=0.1)
        self.assertAlmostEqual(decoded['StateOfCharge'], 75.5, delta=0.5)
        self.assertEqual(decoded['MaxCellTemp'], 44.0)
        self.assertEqual(decoded['DeratingActive'], 1)

if __name__ == '__main__':
    unittest.main()
