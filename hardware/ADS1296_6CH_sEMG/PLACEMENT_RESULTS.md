# Six-target placement check - final CapFix PCB

The specific six-distance check was rerun numerically after the final PCB save, not only visually inspected. All six requested limits pass. Board outline: **100 x 80 mm**; four copper layers; nominal thickness 1.6 mm. The original user-saved A4 PCB is unchanged.

## Measurements

Distances below are the XY distance from the component footprint centre to the centre of the specified U1 pad. They use the same metric as the reported original distances. They are not pad-edge clearances or routed trace lengths.

| Component | U1 pin | Before, mm | After XY, mm | Limit, mm | Assembly face |
|---|---:|---:|---:|---:|---|
| C22 | 48 | 7.84 | 1.9875 | 2.0 | Top |
| C10 | 59 | 5.94 | 1.9875 | 2.0 | Top |
| C14 | 24 | 9.47 | 0.3625 | 2.0 | Underside |
| C20 | 26 | 6.07 | 1.9875 | 2.0 | Top |
| C27 | 54 | 8.96 | 0.0000 | 2.0 | Underside |
| R21 | 61 | 5.73 | 0.8500 | 3.0 | Underside |

C27 is directly behind pin 54 in XY, **not at zero physical or electrical distance**. C14, C27 and R21 connect through one signal layer-change via each. Including nominal board thickness, straight-line surface-to-surface centre distances are approximately 1.641, 1.600 and 1.812 mm respectively; these still are not electrical path lengths. Component body and lead heights are not included in that estimate.

## Connected copper and return paths

| Component | Explicit planar signal centreline, mm | Signal vias | Ground pad centre to local via centre, mm |
|---|---:|---:|---:|
| C22 | 2.381003 | 0 | 0.949977 |
| C10 | 2.381003 | 0 | 0.949977 |
| C14 | 3.110292 | 1 | 1.449968 |
| C20 | 2.381003 | 0 | 0.949977 |
| C27 | 2.639461 | 1 | 1.200000 |
| R21 | 2.550888 | 1 | Not a grounded component |

These lengths follow explicit copper segments between pad centres and exclude vertical travel through vias. Each of the five capacitors has its own declared local GND via, a direct same-face connection to that via, and a via spanning In1.Cu. C14's reference return to U1.25 is also explicitly connected: 3.157805 mm planar centreline and one layer-change via. The independent report checks both terminals of R21 and C23 in the RLD feedback network.

## Assembly and collateral changes

- **C14, C27, R21 and C23 are on the underside.** The other 109 footprints are on top. Existing values and package sizes are retained; no 0402 parts were introduced. Plan soldering access for both faces.
- C23 follows R21 to keep the feedback network compact. C7, C12, C15 and R34 were moved to make room for the requested corrections.
- C152 was absent from the user's saved PCB. It was restored to match the existing schematic and reconnect its dangling routes.
- The MCU socket location, outline and GPIO assignments are unchanged. Most original copper is preserved; CHANGE_AUDIT.json records the exact change scope.

## Verification evidence

- SIX_TARGET_VERIFICATION.json: independent six-limit, outline, connected-path and local-return check; includes execution time and verifier hashes.
- VERIFICATION.json: component/pin/socket/routing audit.
- routed_drc.json: zero design-rule violations, zero unconnected items and zero schematic-parity issues.
- erc.json: zero electrical-rule violations.
- Final PCB SHA256: `adb9748b6987b523c18c6ec353b9b18b20cc3a62a4169fec022da6b388176e3e`.

The checks establish the stated layout geometry and connectivity. They do not measure noise, RLD stability, acquisition reliability or body-connected electrical safety. The 2 mm / 3 mm distances are project constraints; [TI's ADS1296 datasheet](https://www.ti.com/lit/ds/symlink/ads1296.pdf) calls for close capacitor placement and short returns but does not specify these exact centre-distance limits.
