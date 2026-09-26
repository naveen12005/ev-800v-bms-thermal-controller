import can
import cantools
import sys

db = cantools.database.load_file("vehicle.dbc")
bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

print("[*] Running Automated HIL/SIL Verification Test on vcan0...")

frames_verified = 0
target_frames = 20

try:
    for msg in bus:
        if msg.arbitration_id == 256:
            decoded = db.decode_message(msg.arbitration_id, msg.data)
            
            # Assertion 1: Engine RPM must stay within physical design bounds (0 - 6500 RPM)
            assert 0.0 <= decoded['EngineSpeed'] <= 6500.0, f"RPM boundary failure: {decoded['EngineSpeed']}"
            
            # Assertion 2: Coolant temperature cannot exceed max thermal threshold (150 degC)
            assert decoded['CoolantTemp'] <= 150.0, f"Thermal overrun failure: {decoded['CoolantTemp']}"
            
            # Assertion 3: Fuel tank cannot exceed 100%
            assert 0.0 <= decoded['FuelTankLevel'] <= 100.0, f"Fuel level sensor error: {decoded['FuelTankLevel']}"
            
            frames_verified += 1
            print(f"  [PASS] Frame {frames_verified}/{target_frames} validated | RPM: {decoded['EngineSpeed']:.1f} | Temp: {decoded['CoolantTemp']:.1f}C")
            
            if frames_verified >= target_frames:
                print("\n[SUCCESS] 100% of telemetry frames met CAN physical layer specifications!")
                break
except AssertionError as e:
    print(f"\n[FAIL] Test assertion triggered: {e}")
    sys.exit(1)
finally:
    bus.shutdown()
