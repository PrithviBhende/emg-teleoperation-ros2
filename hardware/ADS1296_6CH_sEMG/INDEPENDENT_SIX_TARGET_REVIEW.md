# Independent six-target measurement

`verify_six_targets.py` reloads the saved PCB and independently recomputes C22→U1.48, C10→U1.59, C14→U1.24, C20→U1.26, and C27→U1.54 against a 2.000 mm maximum. R21→U1.61 has a 3.000 mm maximum. These are footprint-centre to ADS1296 pad-centre distances in the XY plane, not body-edge or trace-length measurements. Target pin numbers, nets, and thresholds are hard-coded independently of the placement script.

The report records the final PCB SHA256 and UTC check time, rejects a PCB that changes during measurement, and asserts the closed 100×80 mm rectangular outline. It also verifies explicit signal copper, both ends of R21/C23 feedback, C14's return to VREFN pin 25, and a separate local ground via and explicit same-face return for each of the five capacitors. Coordinates declared in `local_routes.json` are checked; if absent, nearest explicitly connected ground-via inference is disclosed. Native KiCad DRC remains necessary to check filled-plane connectivity, clearances, and all other board nets.

C14, C27, and R21 may be placed on the underside. Their 2D placement limits therefore do **not** imply the same 3D separation or inductance as top-side placement. The report separately shows a straight-line separation estimate including the configured 1.6 mm board thickness, plus explicit planar copper length and series-via count. These values must be kept distinct in any handoff statement. Underside placement also means two-sided assembly; the former “all components on top” claim would no longer apply.

Run the checker after the final routing/save and native DRC, using KiCad's Python:

```text
"C:\Program Files\KiCad\10.0\bin\python.exe" verify_six_targets.py --report SIX_TARGET_VERIFICATION.json
```

A passing report is evidence that these specific geometric and explicit-connectivity checks were rerun. It does not prove noise performance, RLD stability, capacitor effective capacitance, or physical operation. This note intentionally does not declare a final PASS in advance of that run.
