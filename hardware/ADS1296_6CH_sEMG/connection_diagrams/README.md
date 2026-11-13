# Simplified component and connection pictures

Start with **01_main_connections.png**. It follows every electrode pair through its two series resistors per leg and differential capacitor into the ADS1296, then shows the eight wires to the Waveshare ESP32-S3-Tiny with socket contacts and GPIO numbers.

**02_power_and_capacitors.png** shows the regulated 5 V input, fuse, switch/MOSFET, diode, analog regulator, supply rails, bypass/reference capacitors and fixed logic pull resistors.

**03_protection_and_bias.png** expands one complete input protection circuit, identifies the corresponding components for all six channels, and shows the separate RLD/bias electrode circuit.

Each picture is also supplied as an SVG for clear zooming and printing. Pin positions are rearranged for readability: these are electrical connection illustrations, not physical package pinouts or assembly placement drawings. The main picture shows protection taps whose complete wiring is in picture 03. Parallel capacitor groups in picture 02 use the ∥ sign; each capacitor in a group connects across the named rail and GND.

The drawings use a fresh XML netlist exported from the CapFix schematic. `diagram_connection_checks.json` records the checked connection groups and source hash. These checks compare the illustrations to the saved design; they are not a new electrical design review or hardware performance test.

Fal was requested but its generation tools were not exposed in this session and plugin search returned no Fal entry. These pictures were drawn locally from the schematic; no Fal model, request ID or generated output URL exists for them.
