# Siemens NX Open Journal: Optimized Parallel Microchannel Cold Plate
# Generated automatically by Antigravity CAD Agent for 800V EV BMS Project

import NXOpen
import NXOpen.UF

def main():
    theSession = NXOpen.Session.GetSession()
    theUFSession = NXOpen.UF.UFSession.GetUFSession()
    workPart = theSession.Parts.Work

    # 1. Create Base Aluminum Plate
    plate_tag = theUFSession.Modl.CreateBlock1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        [0.0, 0.0, 0.0],
        ["360.0", "330.0", "12.0"]
    )
    theSession.ListingWindow.Open()
    theSession.ListingWindow.WriteLine("Optimized Base Plate Created: 360.0x330.0x12.0 mm")

    # 2. Cut Inlet & Outlet Distribution Manifolds
    active_len = 360.0 - 2 * 15.0
    inlet_manifold = theUFSession.Modl.CreateBlock1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        ["15.0", "15.0", "12.0 - 8.0"],
        ["25.0", str(330.0 - 2 * 15.0), "8.0"]
    )
    theUFSession.Modl.SubtractBodies(plate_tag, inlet_manifold)

    outlet_manifold = theUFSession.Modl.CreateBlock1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        [str(360.0 - 15.0 - 25.0), "15.0", "12.0 - 8.0"],
        ["25.0", str(330.0 - 2 * 15.0), "8.0"]
    )
    theUFSession.Modl.SubtractBodies(plate_tag, outlet_manifold)

    # 3. Cut 24 Parallel Microchannels Between Manifolds
    y_span = 330.0 - 2 * 15.0
    ch_pitch = y_span / 24
    ch_width = ch_pitch - 1.8
    ch_x_start = 15.0 + 25.0
    ch_x_len = 360.0 - 2 * 15.0 - 2 * 25.0

    for i in range(24):
        y_pos = 15.0 + i * ch_pitch
        ch_tag = theUFSession.Modl.CreateBlock1(
            NXOpen.UF.UFModl.FeatureSigns.Nullsign,
            [str(ch_x_start), str(y_pos), "12.0 - 8.0"],
            [str(ch_x_len), str(ch_width), "8.0"]
        )
        theUFSession.Modl.SubtractBodies(plate_tag, ch_tag)

    # 4. Create Inlet & Outlet Boss Ports
    inlet_port = theUFSession.Modl.CreateCyl1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        [15.0 + 25.0/2.0, 15.0 + 15.0, 12.0],
        "18.0", "16.0", [0.0, 0.0, 1.0]
    )
    theUFSession.Modl.UniteBodies(plate_tag, inlet_port)

    outlet_port = theUFSession.Modl.CreateCyl1(
        NXOpen.UF.UFModl.FeatureSigns.Nullsign,
        [360.0 - 15.0 - 25.0/2.0, 330.0 - 15.0 - 15.0, 12.0],
        "18.0", "16.0", [0.0, 0.0, 1.0]
    )
    theUFSession.Modl.UniteBodies(plate_tag, outlet_port)

    theSession.ListingWindow.WriteLine("Optimized Parallel Microchannel Cold Plate CAD completed successfully!")

if __name__ == "__main__":
    main()
