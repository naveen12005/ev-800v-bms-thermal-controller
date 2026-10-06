"""
Upgraded 800V 75kWh Battery Pack Electro-Thermal Plant Simulator
================================================================
Combines:
1. 2RC Thevenin Electrochemical Equivalent Circuit Model (ECM)
   - Dynamic OCV(SOC, T), Ohmic resistance R0, Charge-transfer RC1, Diffusion RC2
2. 2-Node Dual-State Thermal Plant Model:
   - T_core (internal jelly roll / electrode stack)
   - T_surf (aluminum can / thermistor mounting surface)
   - Anisotropic heat conduction (R_cs core-to-surface)
3. CAD-Grounded Liquid Cold Plate Coupling (Baseline Serpentine vs. Optimized Parallel Microchannel):
   - Dynamic heat transfer coefficient h(v_dot)
   - Hydraulic pressure drop (ΔP) & parasitic pump power
   - Cell-to-cell spatial temperature distribution (ΔT_spread)
4. Anode Overpotential & Lithium Plating Invariant Tracker (V_anode vs. Li/Li+)
"""

import math
import os
import json

class BatteryPackPlant:
    def __init__(
        self,
        capacity_kwh=75.0,
        initial_soc=15.0,
        ambient_temp=38.0,
        cooling_type="OPTIMIZED_PARALLEL"
    ):
        self.capacity_kwh = capacity_kwh
        self.capacity_ah = (capacity_kwh * 1000.0) / 800.0  # ~93.75 Ah
        self.soc = float(initial_soc)
        self.ambient_temp = float(ambient_temp)
        self.cooling_type = cooling_type.upper()

        # Dual-Node Thermal States (°C)
        self.temp_core = float(ambient_temp)  # Core internal jelly roll
        self.temp_surf = float(ambient_temp)  # Surface can where thermistors attach
        self.temp_c = float(ambient_temp)     # Backward compatibility alias

        # Thermal masses (J/K) for 75kWh pack
        # Core active material (~380 kg of NMC811 cells, Cp ~ 950 J/kg.K)
        self.c_core = 145000.0
        # Surface casing, busbars, module enclosure (Cp ~ 890 J/kg.K)
        self.c_surf = 45000.0
        # Core-to-surface thermal resistance (K/W across pack)
        self.r_core_to_surf = 0.0035

        # 2RC Equivalent Circuit Model (ECM) States (Volts)
        self.v_rc1 = 0.0  # Activation polarization (fast, ~0.5s tau)
        self.v_rc2 = 0.0  # Concentration / diffusion polarization (slow, ~25s tau)
        self.pack_voltage = 720.0

        # Coolant loop parameters
        self.coolant_temp = 20.0
        self.pump_flow_lpm = 8.0  # Default coolant flow rate
        self.delta_p_kpa = 0.0
        self.pumping_power_w = 0.0
        self.spatial_gradient_c = 0.0

        # Load CAD-calibrated parameters
        self._load_cad_parameters()

    def _load_cad_parameters(self):
        calib_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cad", "cold_plate_thermal_params.json")
        if os.path.exists(calib_file):
            try:
                with open(calib_file, "r") as f:
                    calib = json.load(f)
                key = "baseline" if "BASELINE" in self.cooling_type else "optimized"
                p = calib.get(key, {})
                self.base_conductance = p.get("conductance_w_per_k", 85.0)
                self.base_dp = p.get("pressure_drop_kpa", 21.4)
                self.gradient_factor = 1.35 if "BASELINE" in self.cooling_type else 0.45
            except Exception:
                self._fallback_params()
        else:
            self._fallback_params()

    def _fallback_params(self):
        if "BASELINE" in self.cooling_type:
            self.base_conductance = 70.0
            self.base_dp = 21.5
            self.gradient_factor = 1.35
        else:
            self.base_conductance = 110.0
            self.base_dp = 1.35
            self.gradient_factor = 0.45

    def compute_ecm_parameters(self):
        """
        Computes temperature and SOC-dependent 2RC ECM parameters:
        R0 (Ohmic), R1, C1 (Charge Transfer), R2, C2 (Diffusion)
        """
        temp_k = self.temp_core + 273.15
        # Arrhenius factor for reaction kinetics
        arrh = math.exp(1200.0 * (1.0 / temp_k - 1.0 / 298.15))
        soc_norm = self.soc / 100.0
        soc_stress = 1.0 + 0.40 * ((soc_norm - 0.5) ** 2)

        # Baseline pack parameters (800V 75kWh pack)
        r0 = 0.045 * arrh * soc_stress   # 45 mOhm baseline Ohmic resistance
        r1 = 0.012 * arrh                # 12 mOhm charge transfer
        c1 = 45.0 / max(0.001, arrh)     # ~45 Farad (tau1 = R1*C1 ~ 0.54s)
        r2 = 0.018 * arrh * (1.0 + 0.3 * (1.0 - soc_norm)) # 18 mOhm diffusion
        c2 = 1400.0                      # ~1400 Farad (tau2 = R2*C2 ~ 25s)

        return r0, r1, c1, r2, c2

    def compute_ocv(self):
        """
        Nonlinear Open Circuit Voltage (OCV) curve for NMC811 800V pack (192S).
        Accounts for phase transition plateau between 30% and 70% SOC.
        """
        s = self.soc / 100.0
        # Realistic empirical polynomial fit for 192S NMC811
        v_cell = (
            3.40
            + 0.68 * s
            - 0.35 * (s ** 2)
            + 0.55 * (s ** 3)
            - 0.05 * math.exp(-35.0 * s)
            + 0.04 * math.log(max(0.001, 1.02 - s))
        )
        return max(640.0, min(840.0, v_cell * 192.0))

    def compute_anode_potential(self, current, r0):
        """
        Estimates negative graphite electrode overpotential relative to Li/Li+.
        Fast charging limit: V_anode > 0.05 V to prevent metallic lithium plating.
        """
        soc_norm = self.soc / 100.0
        temp_k = self.temp_core + 273.15
        # Anode equilibrium potential drops as anode fills with lithium
        v_anode_eq = 0.22 - 0.14 * soc_norm
        # Kinetic overpotential under high charge current
        i_cell = current / 2.0  # 2P configuration
        eta_charge_transfer = (i_cell * 0.0012) * math.exp(1500.0 * (1.0 / temp_k - 1.0 / 298.15))
        v_anode = v_anode_eq - eta_charge_transfer
        return v_anode

    def compute_cooling_coupling(self, pump_flow_lpm, chiller_active):
        """
        Dynamic CAD-derived fluid conductance and pressure drop as a function of pump flow.
        """
        flow_ratio = max(0.1, pump_flow_lpm / 8.0)
        # Heat transfer scaling: Nu ~ Re^0.8 for turbulent serpentine, Nu ~ Re^0.5 for laminar microchannel
        if "BASELINE" in self.cooling_type:
            cond = self.base_conductance * (flow_ratio ** 0.8)
            dp = self.base_dp * (flow_ratio ** 1.8)
        else:
            cond = self.base_conductance * (flow_ratio ** 0.6)
            dp = self.base_dp * (flow_ratio ** 1.4)

        # Chiller delivers 12°C glycol if commanded active, else passive 25°C radiator
        self.coolant_temp = 12.0 if chiller_active else max(25.0, self.ambient_temp - 5.0)

        # Parasitic pump power (W)
        v_dot = (pump_flow_lpm / 1000.0) / 60.0
        p_pump = (v_dot * dp * 1000.0) / 0.45

        return cond, dp, p_pump

    def step(self, commanded_current, dt_sec=0.05, pump_flow_lpm=8.0, chiller_active=True):
        r0, r1, c1, r2, c2 = self.compute_ecm_parameters()
        ocv = self.compute_ocv()

        # Update 2RC Polarization Voltages
        self.v_rc1 += ((commanded_current / c1) - (self.v_rc1 / (r1 * c1))) * dt_sec
        self.v_rc2 += ((commanded_current / c2) - (self.v_rc2 / (r2 * c2))) * dt_sec

        # Terminal Voltage: V_term = OCV + I*R0 + V_rc1 + V_rc2
        self.pack_voltage = ocv + (commanded_current * r0) + self.v_rc1 + self.v_rc2

        # Anode overpotential check
        v_anode = self.compute_anode_potential(commanded_current, r0)

        # Thermal Physics:
        # Joule heat (core) + Entropic reversible heat
        p_joule = (commanded_current ** 2) * r0 + (self.v_rc1 ** 2) / r1 + (self.v_rc2 ** 2) / r2
        entropic_coeff = -0.00015  # V/K (endothermic at low SoC, exothermic at high SoC)
        p_entropic = commanded_current * (self.temp_core + 273.15) * entropic_coeff * 192.0
        p_gen_core = max(0.0, p_joule + p_entropic)

        # Dynamic cooling loop coupling
        cond, dp, p_pump = self.compute_cooling_coupling(pump_flow_lpm, chiller_active)
        self.delta_p_kpa = dp
        self.pumping_power_w = p_pump

        # Core-to-Surface Heat Flow: Q_cs = (T_core - T_surf) / R_cs
        q_core_to_surf = (self.temp_core - self.temp_surf) / self.r_core_to_surf

        # Surface-to-Coolant Heat Dissipation: Q_diss = K_cond * (T_surf - T_coolant)
        q_surf_to_coolant = cond * max(0.0, self.temp_surf - self.coolant_temp)

        # Dual-State ODE updates
        d_temp_core = (p_gen_core - q_core_to_surf) * (dt_sec / self.c_core)
        d_temp_surf = (q_core_to_surf - q_surf_to_coolant) * (dt_sec / self.c_surf)

        self.temp_core += d_temp_core
        self.temp_surf += d_temp_surf
        self.temp_c = self.temp_surf  # Thermistor reading

        # Spatial module gradient
        delta_t_fluid = p_gen_core / max(1.0, (pump_flow_lpm / 60.0 * 1.065 * 3320.0))
        self.spatial_gradient_c = delta_t_fluid * self.gradient_factor

        # Coulomb Counting SoC update
        coulombs = commanded_current * dt_sec
        self.soc += (coulombs / (self.capacity_ah * 3600.0)) * 100.0
        self.soc = min(100.0, max(0.0, self.soc))

        return {
            'voltage': self.pack_voltage,
            'current': commanded_current,
            'soc': self.soc,
            'temp': self.temp_surf,             # Thermistor casing reading (°C)
            'temp_core': self.temp_core,        # Estimated internal jelly roll (°C)
            'delta_t_core_surf': self.temp_core - self.temp_surf,
            'spatial_gradient_c': self.spatial_gradient_c,
            'anode_potential': v_anode,         # Volts vs Li/Li+ (>0.05V safe)
            'r_int_mohm': r0 * 1000.0,
            'v_rc1': self.v_rc1,
            'v_rc2': self.v_rc2,
            'cooling_type': self.cooling_type,
            'pressure_drop_kpa': self.delta_p_kpa,
            'pumping_power_w': self.pumping_power_w
        }
