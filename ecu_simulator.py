import time
import can
import cantools

# 1. Load CAN database
db = cantools.database.load_file("vehicle.dbc")
msg_engine = db.get_message_by_name("K15B_EngineStatus")
msg_dynamics = db.get_message_by_name("K15B_VehicleDynamics")

# 2. Attach to SocketCAN interface (using modern 'interface' parameter)
bus = can.Bus(channel='vcan0', interface='socketcan')

# Initial Physical Parameters (Ambient State)
coolant_temp = 28.0      # Ambient start temp in deg C
fuel_pct = 100.0         # 45L tank at full capacity
vehicle_speed = 0.0      # Stationary
engine_rpm = 1100.0      # Cold start fast-idle
throttle = 5.0           # Baseline idle throttle %

print("[*] DENSO ECM Simulator (K15B 1.5L Petrol) Online on vcan0...")
print("[*] Broadcasting cyclic telemetry (100ms cycle)... Press Ctrl+C to stop.")

cycle_count = 0
try:
    while True:
        cycle_count += 1

        # Phase 1: Cold start warmup (first 5 seconds / 50 cycles)
        if cycle_count < 50:
            engine_rpm = max(750.0, engine_rpm - 7.0)
            coolant_temp = min(90.0, coolant_temp + 1.2)
            vehicle_speed = 0.0
            throttle = 5.0
        # Phase 2: Drive cycle (Acceleration & Gear Shifts)
        else:
            throttle = 45.0  # Driver inputs 45% pedal demand
            coolant_temp = min(91.5, coolant_temp + 0.05)
            
            # Accelerate vehicle speed up to 80 km/h
            vehicle_speed = min(80.0, vehicle_speed + 0.4)
            
            # Simulate 5-speed manual gear shift drops
            if vehicle_speed < 25.0:
                engine_rpm = 750.0 + (vehicle_speed * 110)      # 1st Gear
            elif vehicle_speed < 45.0:
                engine_rpm = 1400.0 + ((vehicle_speed - 25) * 80) # 2nd Gear
            else:
                engine_rpm = 1800.0 + ((vehicle_speed - 45) * 55) # 3rd Gear

        # Dynamic fuel burn calculation: proportional to RPM and Throttle load
        fuel_burn_rate = (engine_rpm / 6200.0) * (throttle / 100.0) * 0.015
        fuel_pct = max(0.0, fuel_pct - fuel_burn_rate)

        # Bit-pack signals according to K15B DBC rules
        engine_data = msg_engine.encode({
            'EngineSpeed': engine_rpm,
            'CoolantTemp': coolant_temp,
            'ThrottlePosition': throttle,
            'FuelTankLevel': fuel_pct
        })

        dynamics_data = msg_dynamics.encode({
            'VehicleSpeed': vehicle_speed
        })

        # Broadcast frames onto CAN bus (ID 0x100 and 0x101)
        bus.send(can.Message(arbitration_id=msg_engine.frame_id, data=engine_data, is_extended_id=False))
        bus.send(can.Message(arbitration_id=msg_dynamics.frame_id, data=dynamics_data, is_extended_id=False))

        time.sleep(0.1)  # 100ms cyclic rate

except KeyboardInterrupt:
    print("\n[!] Ignition off. ECU simulation stopped.")
finally:
    bus.shutdown()
