import time
import math
import can
import cantools

# Load the CAN database definition
db = cantools.database.load_file("vehicle.dbc")
engine_msg = db.get_message_by_name("EngineData")
speed_msg = db.get_message_by_name("VehicleSpeedData")

# Connect to SocketCAN interface
bus = can.interface.Bus(channel='vcan0', bustype='socketcan')
print("[*] Engine ECU Simulator broadcasting on vcan0... (Press Ctrl+C to stop)")

t = 0.0
try:
    while True:
        # Dynamic driving telemetry
        sim_speed = 60.0 + 30.0 * math.sin(t * 0.5)
        sim_rpm = 1200.0 + (sim_speed * 35.0)
        sim_temp = 88.0 + 2.0 * math.sin(t * 0.1)
        sim_throttle = max(0.0, min(100.0, (sim_rpm / 4000.0) * 100))

        # Encode engineering units into bit-packed CAN payloads
        engine_payload = engine_msg.encode({
            'EngineSpeed': sim_rpm,
            'EngineTemp': sim_temp,
            'ThrottlePos': sim_throttle
        })

        speed_payload = speed_msg.encode({
            'VehicleSpeed': sim_speed
        })

        # Broadcast frames
        msg1 = can.Message(arbitration_id=engine_msg.frame_id, data=engine_payload, is_extended_id=False)
        msg2 = can.Message(arbitration_id=speed_msg.frame_id, data=speed_payload, is_extended_id=False)

        bus.send(msg1)
        bus.send(msg2)

        t += 0.1
        time.sleep(0.1)  # 100ms cycle time

except KeyboardInterrupt:
    print("\n[!] Transmitter stopped.")
finally:
    bus.shutdown()
