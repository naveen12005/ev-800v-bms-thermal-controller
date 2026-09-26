import can
import cantools

db = cantools.database.load_file("vehicle.dbc")
bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

print("[*] Telemetry Receiver listening on vcan0... (Press Ctrl+C to stop)\n")

try:
    for message in bus:
        try:
            decoded = db.decode_message(message.arbitration_id, message.data)
            msg_name = db.get_message_by_frame_id(message.arbitration_id).name
            print(f"[{msg_name}] ID: 0x{message.arbitration_id:03X} -> {decoded}")
        except KeyError:
            pass
except KeyboardInterrupt:
    print("\n[!] Receiver stopped.")
finally:
    bus.shutdown()
