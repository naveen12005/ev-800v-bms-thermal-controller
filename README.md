# K15B Engine CAN Telemetry & Diagnostics Emulator

An in-vehicle networking simulation environment modeling the Maruti/Denso K15B 1.5L naturally aspirated powertrain over Linux SocketCAN.

## Features
- **DBC Specification:** Custom CAN database (vehicle.dbc) defining physical layer signal scaling, offsets, and bit packing for engine dynamics.
- **Physical State Modeling:** Simulates cold-start fast idle, thermal stabilization (ambient to 90°C), manual gear shift progression, and load-proportional fuel consumption.
- **Verification Suite:** Automated frame validation pipeline checking signal limits against automotive safety margins.

## How to Run
```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan && sudo ip link set up vcan0
python3 ecu_simulator.py &
python3 test_pipeline.py
```
