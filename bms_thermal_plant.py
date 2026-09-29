import math

class BatteryPackPlant:
    def __init__(self, capacity_kwh=75.0, initial_soc=15.0, ambient_temp=38.0):
        self.capacity_ah = (capacity_kwh * 1000.0) / 800.0  # ~93.75 Ah
        self.soc = initial_soc
        self.temp_c = ambient_temp
        self.pack_voltage = 720.0
        self.thermal_mass_j_per_k = 180000.0   # Thermal capacity of pack
        self.cooling_conductance = 85.0        # W/K heat dissipation to active cooling loop
        self.coolant_temp = 20.0

    def compute_internal_resistance(self):
        # Arrhenius kinetics: resistance increases at cold temps and extreme high/low SoC
        base_r = 0.055  # 55 mOhm pack baseline
        temp_k = self.temp_c + 273.15
        arrhenius_factor = math.exp(1200.0 * (1.0 / temp_k - 1.0 / 298.15))
        soc_factor = 1.0 + 0.35 * ((self.soc / 100.0 - 0.5) ** 2)
        return base_r * arrhenius_factor * soc_factor

    def compute_ocv(self):
        # Nominal 800V architecture: 680V (empty) to 840V (fully charged)
        return 680.0 + (160.0 * (self.soc / 100.0))

    def step(self, commanded_current, dt_sec=0.05):
        r_int = self.compute_internal_resistance()
        ocv = self.compute_ocv()
        
        # Terminal voltage with ohmic drop
        self.pack_voltage = ocv + (commanded_current * r_int)

        # Joule heating P = I^2 * R
        joule_heat_w = (commanded_current ** 2) * r_int
        cooling_w = self.cooling_conductance * max(0.0, self.temp_c - self.coolant_temp)
        net_heat_w = joule_heat_w - cooling_w

        # Thermal rate of change
        delta_temp = (net_heat_w * dt_sec) / self.thermal_mass_j_per_k
        self.temp_c += delta_temp

        # Coulomb counting SoC update
        coulombs = commanded_current * dt_sec
        self.soc += (coulombs / (self.capacity_ah * 3600.0)) * 100.0
        self.soc = min(100.0, max(0.0, self.soc))

        return {
            'voltage': self.pack_voltage,
            'current': commanded_current,
            'soc': self.soc,
            'temp': self.temp_c,
            'r_int_mohm': r_int * 1000.0
        }
