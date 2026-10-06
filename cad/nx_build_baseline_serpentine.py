# Siemens NX Open Journal: Baseline Serpentine Cold Plate
# Generated automatically by Antigravity CAD Agent for 800V EV BMS Project

import NXOpen
import NXOpen.UF
import math

def main():
    theSession = NXOpen.Session.GetSession()
    theUFSession = NXOpen.UF.UFSession.GetUFSession()
    workPart = theSession.Parts.Work

    # 1. Create Base Aluminum Plate Extrusion
    plate_tag = theUFSession.Modl.CreateBlock1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        [0.0, 0.0, 0.0],
        ["360.0", "330.0", "12.0"]
    )
    theSession.ListingWindow.Open()
    theSession.ListingWindow.WriteLine("Base Aluminum 6061 Plate Created: 360.0x330.0x12.0 mm")

    # 2. Cut Serpentine Fluid Channel Pocket
    # Passes at regular pitch across Y-axis
    y_pitch = (330.0 - 2 * 20.0) / 6
    for i in range(6):
        y_pos = 20.0 + i * y_pitch
        pass_len = 360.0 - 2 * 20.0
        pass_tag = theUFSession.Modl.CreateBlock1(
            NXOpen.UF.UFModl.FeatureSigns.Nullsign,
            [20.0, y_pos, 12.0 - 7.0],
            [str(pass_len), "14.0", "7.0"]
        )
        theUFSession.Modl.SubtractBodies(plate_tag, pass_tag)

    # 3. Add Inlet & Outlet Ports
    inlet_boss = theUFSession.Modl.CreateCyl1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        [20.0 + 10.0, 20.0 + 7.0, 12.0],
        "18.0", "16.0", [0.0, 0.0, 1.0]
    )
    theUFSession.Modl.UniteBodies(plate_tag, inlet_boss)

    outlet_boss = theUFSession.Modl.CreateCyl1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        [360.0 - 20.0 - 10.0, 330.0 - 20.0 - 7.0, 12.0],
        "18.0", "16.0", [0.0, 0.0, 1.0]
    )
    theUFSession.Modl.UniteBodies(plate_tag, outlet_boss)

    theSession.ListingWindow.WriteLine("Baseline Serpentine Cold Plate CAD construction complete!")

if __name__ == "__main__":
    main()
