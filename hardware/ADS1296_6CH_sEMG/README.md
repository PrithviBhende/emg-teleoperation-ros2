# A4 TinySocket CapFix - corrected local capacitor and RLD placement

Open ADS1296_RevA4_TinySocket.kicad_pro **inside this CapFix folder** in KiCad 10.0.3 or newer. This is a separate revision based on the user's saved A4 board. The original A4 board and the A3 project are untouched.

The six requested placement limits have been rechecked numerically on the final saved PCB. See [PLACEMENT_RESULTS.md](PLACEMENT_RESULTS.md) for the measurements, trace lengths and assembly changes. The board remains 100 x 80 mm with the same removable Tiny socket. **C14, C27, R21 and its companion C23 now mount on the underside; all other components mount on top.**

## What the small capacitor holes do

The original small 0.3 mm drill holes are plated vias: copper tunnels linking board layers. Most near the bypass capacitors provide short ground-plane returns. Others carry supply or signal connections. They are not mounting holes or connector sockets, and do not require inserting a component. They are retained in this revision.

The MCU attachment now uses larger **1.0 mm finished plated-through-hole targets with 1.8 mm lands** for soldered female sockets. Bare holes alone do not make a reliable removable electrical connection.

## New removable attachment

- Same preassembled **Waveshare ESP32-S3-Tiny, SKU27069**, or **Tiny-Kit SKU27070** including the USB-C adapter and FPC. Not ESP32-S3-MINI-1 or ESP32-S3-Zero.
- **Two 1x9 female sockets** solder onto this carrier, and **two 1x9 male headers** solder to the Tiny's side holes. The Tiny then plugs into the carrier. This requires one-time soldering, not solderless insertion of loose pins into holes.
- **2.54 mm contact pitch; 15.24 mm between row centres**, calculated from the manufacturer's 18 mm body and symmetrical 1.38 mm edge offsets. First row centres are 1.59 mm below the top of the Tiny; the nine contacts span 20.32 mm. The five bottom contacts and underside pads are not used.
- Component A1 is a composite socket/module assembly: its 18 footprint pads represent the two nine-contact female strips. Order both strips and both male headers in addition to the Tiny kit; A1 is not one off-the-shelf 18-pin connector.
- Dimensional reference parts: **2x Harwin M20-7820942 female**, **2x Harwin M20-9990945 male**. The socket is 8.5 mm high and mates with 0.64 mm square pins. Standard equivalents are acceptable only after checking pin size, footprint and housing dimensions; prices and Indian stock were not checked in this revision.
- The header assembly adds height: approximately 11 mm from carrier top to Tiny underside, based on 8.5 mm socket height plus 2.54 mm male-header housing. Confirm actual seating and enclosure clearance.

**Mechanical qualification is still required:** Waveshare's drawing specifies the pitch but not the finished hole diameter/tolerance. We cannot certify that these male pins fit the purchased Tiny without a measurement or vendor confirmation. Do not drill/enlarge its plated holes to force a fit. Print SOCKET_TEMPLATE_1TO1.svg at 100%, check the 10 mm ruler, and compare an actual Tiny before ordering the carrier. Also check that the male-header plastic clears components on the Tiny underside.

**Power off before insertion/removal. These connectors are unkeyed.** Align the Tiny's 5V pad with carrier pad1, towards the antenna/top edge. Reverse insertion or a one-position offset can damage both boards. Support the carrier when inserting/removing; pull both sides evenly without pulling the FPC cable. Add nonconductive mechanical retention for a wearable enclosure, with no metal against the antenna.

## GPIO changes - update firmware

| Signal | A3 GPIO | A4 socket GPIO | Tiny side contact |
|---|---:|---:|---:|
| CS | 10 | **2** | 5 |
| MOSI / ADS DIN | 11 | **1** | 4 |
| SCLK | 12 | 12 | 18 |
| MISO / ADS DOUT | 13 | 13 | 17 |
| DRDY | 14 | 14 | 16 |
| START | 15 | 15 | 15 |
| PWDN_N | 16 | 16 | 14 |
| RESET_N | 17 | 17 | 13 |

GPIO1/2 are available side contacts and avoid the USB/strapping/PSRAM pins. Native USB still travels over the Tiny's supplied FPC to its kit adapter, not through this carrier. This CapFix retains the A4 socket position, GPIO assignments, existing component values and packages. Local analogue/supply/reference/RLD placement and routing have changed to meet the six limits; physical behaviour has not been measured.

Target remains six channels at **4,000 samples/s per channel**: 21-byte ADS frame gives 84,000 bytes/s before framing. Proposed 4 MHz SPI reads the 168-bit frame in 42 us out of a 250 us period. These calculations do not prove lossless acquisition. Firmware and a sustained sequence-counter capture test remain separate work. No firmware is included here.

## Carrier and connections retained

- 100 x 80 mm, four copper layers, 1.6 mm nominal thickness. F.Cu components/signals; In1.Cu ground reference with no routed tracks; In2.Cu analogue AVDD pour and selected signals; B.Cu selected signals and four SMD components. The antenna keepout remains.
- 109 footprints are on top; C14, C27, R21 and C23 are on the underside. This requires two-sided assembly, including soldering the through-hole sockets/connectors from below. Resistors/capacitors remain 0805 or larger. The ADS1296 still needs careful 0.5 mm-pitch TQFP soldering. See both assembly drawings before soldering; underside drawings are mirrored for viewing from below.
- J1: pin1 regulated 5.0-5.25 V, pin2 GND; not a raw Li-ion cell input. No charger. SW1 controls only the battery branch; USB can still power the system.
- J2-J7: respective CH1-CH6 electrode connectors. Pin1=P, pin2=N, pin3=NC. The retained schematic value says SHIELD but pin3 is not connected.
- J8: pin1 bias/RLD output, pin2=NC. Six pairs plus a separate bias use 13 electrodes.
- Tiny supplies digital 3.3 V. LP5907 separately supplies AVDD. Do not parallel regulator outputs or add external 3.3 V to the Tiny output.
- Input network: 22k + 24.9k in each leg and 1.8nF differential capacitor. Ideal RC pole remains 942.6 Hz, not a 20-450 Hz band-pass or mains notch. Later software filtering is separate.
- Reference, VCAP and RLD values are unchanged. RLD starts disabled; verify it on dummy electrode/cable loads before enabling it for recordings. All six requested XY footprint-centre to U1-pad-centre limits now pass. These are placement distances, not copper lengths: underside parts add layer-change vias and board thickness. Each of the five capacitors has a distinct nearby ground via with an explicit short local return.

## Validation and files

Native ERC/DRC, a socket/pin/route audit and a separate six-target measurement check are included. Check VERIFICATION.json, SIX_TARGET_VERIFICATION.json, routed_drc.json and erc.json. CHANGE_AUDIT.json records changes relative to the preserved user-saved A4 board, including restoration of missing C152 to match the schematic. The final PCB SHA256 in the reports identifies the exact checked design. The dimensional template is nominal, not a measured fit test.

ROUTING_TOP/BOTTOM and ASSEMBLY_TOP/BOTTOM are supplied as SVG and PNG. ASSEMBLY_POSITIONS.pos lists component positions and faces. The fabrication_review folder contains newly exported copper, mask, silkscreen, paste and drill files for this exact revision, including the backside SMD layers. PACKAGE_SHA256.json identifies the packaged files.

The schematic_images folder contains all seven schematic sheets as PNG pictures for quick viewing and SVG files for zooming or printing without loss of detail.

The connection_diagrams folder contains three simpler, labelled component-and-wire pictures: main electrode/MCU connections, power and capacitors, and input protection/body bias. These were drawn locally from a fresh schematic netlist and include a connection-check report. Pin positions are rearranged for readability; use the PCB assembly drawings for physical placement.

This is a **review/bench prototype**. No physical noise, RLD-stability, pin-fit, thermal, USB, connector-life or human-safety test has been performed. The supplied Gerbers/drills are for review until mechanical/assembly and fabricator stack-up checks are complete. Do not mix these files with earlier A3 or A4 exports. Passing geometric/electrical-rule checks does not demonstrate measured noise performance or lossless acquisition.

**No galvanic isolation is fitted. Do not attach a person while USB, a charger, an earthed oscilloscope or other externally grounded equipment is connected.** A reviewed body-connected safety arrangement is required before human recordings.

## Primary sources

- [Waveshare product and dimension drawing](https://docs.waveshare.com/ESP32-S3-Tiny): Tiny geometry and side-contact pitch. The local sources folder contains the published dimension image and pinout.
- [Waveshare kit and castellated-board description](https://www.waveshare.com/product/esp32-s3-tiny.htm).
- [Harwin M20-7820942 socket](https://www.harwin.com/products/M20-7820942): 9 positions, 2.54 mm pitch, 8.5 mm height, 0.64 mm square mating pin.
- [Harwin M20-9990945 header](https://www.harwin.com/products/M20-9990945): 9 positions, 2.54 mm pitch, 0.64 mm square pin, 6.1 mm mating length.
- [TI ADS1296 datasheet](https://www.ti.com/lit/ds/symlink/ads1296.pdf): local capacitor placement and short ground returns. The numerical 2 mm / 3 mm limits are this project's requested constraints, not a quoted TI maximum. TI ADS129x, LP5907 and protection-device data sheets are in the sources folder; part-specific links are in BOM.md.

Do not run the build scripts simply to open the finished project. tighten_layout.py, route_local.py and finish_capfix.py are development tools, not project entry points; rerunning them can overwrite finished routing and requires intermediate workspace files. The project opens directly in KiCad. Independent verification and all exports must be rerun after any PCB edit.
