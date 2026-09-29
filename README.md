\# 800V High-Power EV BMS \& Fast-Charging Thermal Derating Controller



An advanced Battery Management System (BMS) modeling an 800V, 75 kWh liquid-cooled battery pack with dynamic electro-thermal physics and automated ASIL-D safety derating under 350 kW DC ultra-fast charging.



\## System Architecture



```text

+-------------------------------------------------------------+

|             DC Fast Charger (350 kW Dispenser)              |

|   - Dynamically modulates output current (0 - 430A)         |

|   - Respects BMS current limits via CAN arbitration ID 0x211|

+------------------------------+------------------------------+

&#x20;                              |

&#x20;                  CAN 0x211: BMS\_ChargeLimits

&#x20;                  (MaxAllowableCurrent, Gradient)

&#x20;                              v

&#x20;   ======================= vcan0 =======================

&#x20;                              ^

&#x20;                  CAN 0x210: BMS\_PackMetrics

&#x20;                  (PackVoltage, PackCurrent, Temp, SoC)

&#x20;                              |

+------------------------------+------------------------------+

|            800V BMS Controller \& Thermal Plant              |

|  - Closed-Loop Multi-Stage Thermal \& Gradient Derating      |

|  - Dynamic Arrhenius Internal Resistance Modeling           |

|  - Constant Current / Constant Voltage (CC-CV) Handover     |

|  - Slew-rate limiting (150 A/s) to mitigate inductive spikes|

+-------------------------------------------------------------+

