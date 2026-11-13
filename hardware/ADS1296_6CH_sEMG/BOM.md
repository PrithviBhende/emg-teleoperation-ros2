# A4S Tiny carrier CapFix - complete BOM

C14, C27, R21 and C23 mount on B.Cu (underside); all other carrier components mount on F.Cu (top). Plan for two-sided assembly. Resistors/capacitors remain 0805 or larger. U1 still requires 0.5mm-pitch soldering. Component values and packages are unchanged from A4; refer to both assembly drawings for positions.

|Ref|Value / exact MPN|Footprint|Purpose / electrical rating|Source|
|---|---|---|---|---|
|J1|REGULATED 5V IN / B2B-XH-A(LF)(SN)|Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical|5.0-5.25V regulated source, not raw Li-ion; use battery OR USB for initial tests|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf)|
|F1|750mA PTC / MF-MSMF075-2|Fuse:Fuse_1812_4532Metric|0.75A hold / 1.5A trip,13.2V; battery branch only|[Manufacturer](https://www.bourns.com/docs/product-datasheets/mfmsmf.pdf)|
|SW1|BATTERY ENABLE / JS102011SAQN|Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN|SPDT switches MOSFET gate only; USB stays powered with switch OFF|[Manufacturer](https://www.ckswitches.com/media/1422/js.pdf)|
|Q1|AO3401A / AO3401A|Package_TO_SOT_SMD:SOT-23|S=2, D=3, G=1; P-channel battery high-side switch|[Manufacturer](https://www.aosmd.com/pdfs/datasheet/AO3401A.pdf)|
|R47|100k / RC0805FR-07100KL|Resistor_SMD:R_0805_2012Metric|100k; 1%; 0805; 0.125W; >=50V; Default battery OFF|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|D1|SS14 / SS14|Diode_SMD:D_SMA|Cathode1=VSYS,anode2=BAT_SWITCHED; blocks USB backfeed to battery|[Manufacturer](https://www.diodes.com/assets/Datasheets/ds23001.pdf)|
|C1|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Additional carrier bypass; Tiny has its own 10uF input capacitor|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|U2|LP5907MFX-3.3/NOPB / LP5907MFX-3.3/NOPB|Package_TO_SOT_SMD:SOT-23-5|3.3V 250mA low-noise LDO; SOT23-5; analogue supply only|[Manufacturer](https://www.ti.com/lit/ds/symlink/lp5907.pdf)|
|C2|2u2 / C0805C225K4RACTU|Capacitor_SMD:C_0805_2012Metric|2u2; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C225K4RACTU)|
|C3|2u2 / C0805C225K4RACTU|Capacitor_SMD:C_0805_2012Metric|2u2; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C225K4RACTU)|
|TP1|AVDD|TestPoint:TestPoint_Pad_D1.5mm|Analogue 3.3V test point|Mechanical|
|TP2|VSYS|TestPoint:TestPoint_Pad_D1.5mm|5V rail after source diodes|Mechanical|
|C27|1u / C0805C105K4RACTU|Capacitor_SMD:C_0805_2012Metric|1u; X7R 10% 16V; Local AVDD1 pin54 bulk|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C105K4RACTU)|
|C5|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Local U1 pin 19 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C6|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Local U1 pin 21 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C7|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Local U1 pin 22 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C8|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Local U1 pin 54 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C9|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Local U1 pin 56 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C10|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Local U1 pin 59 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C11|1u / C0805C105K4RACTU|Capacitor_SMD:C_0805_2012Metric|1u; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C105K4RACTU)|
|C12|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; U1 pin48 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C13|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; U1 pin50 bypass|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|U1|ADS1296IPAG / ADS1296IPAG|Package_QFP:TQFP-64_10x10mm_P0.5mm|All 64 pins transcribed from TI SBAS459K pp10-11; non-respiration 6-channel version|[Manufacturer](https://www.ti.com/lit/ds/symlink/ads1298.pdf)|
|C14|10u / C1206C106K4PACTU|Capacitor_SMD:C_1206_3216Metric|10u; X5R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C1206C106K4PACTU)|
|C15|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C16|22u / C1210C226K4PACTU|Capacitor_SMD:C_1210_3225Metric|22u; X5R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C1210C226K4PACTU)|
|C17|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|C18|1u / C0805C105K4RACTU|Capacitor_SMD:C_0805_2012Metric|1u; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C105K4RACTU)|
|C19|1u / C0805C105K4RACTU|Capacitor_SMD:C_0805_2012Metric|1u; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C105K4RACTU)|
|C20|1u / C0805C105K4RACTU|Capacitor_SMD:C_0805_2012Metric|1u; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C105K4RACTU)|
|C21|1n / C0805C102J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n; C0G 5% 50V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C102J5GACTU)|
|C22|1u / C0805C105K4RACTU|Capacitor_SMD:C_0805_2012Metric|1u; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C105K4RACTU)|
|R10|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; Unused ADS GPIO pulldown; leave configured as input|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R11|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; Unused ADS GPIO pulldown; leave configured as input|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R12|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; Unused ADS GPIO pulldown; leave configured as input|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R13|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; Unused ADS GPIO pulldown; leave configured as input|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R14|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; |[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R15|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; 10k pulldown; optional clock output remains disabled|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|TP3|VREFP|TestPoint:TestPoint_Pad_D1.5mm|Bench test point; use high impedance probe|Mechanical|
|TP4|VCAP1|TestPoint:TestPoint_Pad_D1.5mm|Bench test point; use high impedance probe|Mechanical|
|TP5|ADS_DRDY_N|TestPoint:TestPoint_Pad_D1.5mm|Bench test point; use high impedance probe|Mechanical|
|J2|CH1: P / N / SHIELD / B3B-PH-K-S(LF)(SN)|Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical|JST PH 3-pin; pin1 positive electrode, pin2 negative electrode, pin3 shield (NC A4S)|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)|
|R111|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R112|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|U3|TPD4E001DBVR / TPD4E001DBVR|Package_TO_SOT_SMD:SOT-23-6|FIT. Input clamps after connector-series 22k; max leakage rating is not a typical noise promise|[Manufacturer](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf)|
|R113|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R114|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|C111|1n8 / C0805C182J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n8; C0G 5% 50V; 1.8 nF, C0G, 5%, 50 V, 0805; differential capacitor, not a cap to ground|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C182J5GACTU)|
|C112|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; 100 nF 16 V X7R bypass at TPD4E001 VCC pin5|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|J3|CH2: P / N / SHIELD / B3B-PH-K-S(LF)(SN)|Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical|JST PH 3-pin; pin1 positive electrode, pin2 negative electrode, pin3 shield (NC A4S)|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)|
|R121|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R122|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|U4|TPD4E001DBVR / TPD4E001DBVR|Package_TO_SOT_SMD:SOT-23-6|FIT. Input clamps after connector-series 22k; max leakage rating is not a typical noise promise|[Manufacturer](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf)|
|R123|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R124|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|C121|1n8 / C0805C182J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n8; C0G 5% 50V; 1.8 nF, C0G, 5%, 50 V, 0805; differential capacitor, not a cap to ground|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C182J5GACTU)|
|C122|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; 100 nF 16 V X7R bypass at TPD4E001 VCC pin5|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|J4|CH3: P / N / SHIELD / B3B-PH-K-S(LF)(SN)|Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical|JST PH 3-pin; pin1 positive electrode, pin2 negative electrode, pin3 shield (NC A4S)|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)|
|R131|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R132|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|U5|TPD4E001DBVR / TPD4E001DBVR|Package_TO_SOT_SMD:SOT-23-6|FIT. Input clamps after connector-series 22k; max leakage rating is not a typical noise promise|[Manufacturer](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf)|
|R133|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R134|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|C131|1n8 / C0805C182J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n8; C0G 5% 50V; 1.8 nF, C0G, 5%, 50 V, 0805; differential capacitor, not a cap to ground|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C182J5GACTU)|
|C132|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; 100 nF 16 V X7R bypass at TPD4E001 VCC pin5|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|J5|CH4: P / N / SHIELD / B3B-PH-K-S(LF)(SN)|Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical|JST PH 3-pin; pin1 positive electrode, pin2 negative electrode, pin3 shield (NC A4S)|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)|
|R141|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R142|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|U6|TPD4E001DBVR / TPD4E001DBVR|Package_TO_SOT_SMD:SOT-23-6|FIT. Input clamps after connector-series 22k; max leakage rating is not a typical noise promise|[Manufacturer](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf)|
|R143|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R144|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|C141|1n8 / C0805C182J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n8; C0G 5% 50V; 1.8 nF, C0G, 5%, 50 V, 0805; differential capacitor, not a cap to ground|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C182J5GACTU)|
|C142|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; 100 nF 16 V X7R bypass at TPD4E001 VCC pin5|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|J6|CH5: P / N / SHIELD / B3B-PH-K-S(LF)(SN)|Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical|JST PH 3-pin; pin1 positive electrode, pin2 negative electrode, pin3 shield (NC A4S)|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)|
|R151|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R152|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|U7|TPD4E001DBVR / TPD4E001DBVR|Package_TO_SOT_SMD:SOT-23-6|FIT. Input clamps after connector-series 22k; max leakage rating is not a typical noise promise|[Manufacturer](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf)|
|R153|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R154|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|C151|1n8 / C0805C182J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n8; C0G 5% 50V; 1.8 nF, C0G, 5%, 50 V, 0805; differential capacitor, not a cap to ground|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C182J5GACTU)|
|C152|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; 100 nF 16 V X7R bypass at TPD4E001 VCC pin5|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|J7|CH6: P / N / SHIELD / B3B-PH-K-S(LF)(SN)|Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical|JST PH 3-pin; pin1 positive electrode, pin2 negative electrode, pin3 shield (NC A4S)|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)|
|R161|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R162|22k / RT0805BRD0722KL|Resistor_SMD:R_0805_2012Metric|22k; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|U8|TPD4E001DBVR / TPD4E001DBVR|Package_TO_SOT_SMD:SOT-23-6|FIT. Input clamps after connector-series 22k; max leakage rating is not a typical noise promise|[Manufacturer](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf)|
|R163|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|R164|24k9 / RT0805BRD0724K9L|Resistor_SMD:R_0805_2012Metric|24k9; 0.1%, <=25 ppm/K; 0805; 0.125W; >=50V; |[Manufacturer](https://yageogroup.com/content/datasheet/asset/file/pyu-rt_1-to-0-01_rohs_l)|
|C161|1n8 / C0805C182J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n8; C0G 5% 50V; 1.8 nF, C0G, 5%, 50 V, 0805; differential capacitor, not a cap to ground|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C182J5GACTU)|
|C162|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; 100 nF 16 V X7R bypass at TPD4E001 VCC pin5|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|R21|1M / RC0805FR-071ML|Resistor_SMD:R_0805_2012Metric|1M; 1%; 0805; 0.125W; >=50V; 1 MOhm 1% 0805; TI typical feedback value|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|C23|1n5 / C0805C152J5GACTU|Capacitor_SMD:C_0805_2012Metric|1n5; C0G 5% 50V; 1.5 nF 5% C0G 50 V; parallel feedback; TI typical value|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C152J5GACTU)|
|R22|110k / RC0805FR-07110KL|Resistor_SMD:R_0805_2012Metric|110k; 1%; 0805; 0.125W; >=50V; 110k 1% 0805; first RLD output series resistor|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R23|110k / RC0805FR-07110KL|Resistor_SMD:R_0805_2012Metric|110k; 1%; 0805; 0.125W; >=50V; 110k 1% 0805; second RLD output series resistor|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|J8|BIAS: 1=RLD 2=NC / B2B-PH-K-S(LF)(SN)|Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical|Separate body bias pad; pin2 open. Connector differs from 3-pin sensing connectors.|[Manufacturer](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf)|
|U9|TPD4E001DBVR / TPD4E001DBVR|Package_TO_SOT_SMD:SOT-23-6|Bias clamp between two 110k resistors; unused IO2 open|[Manufacturer](https://www.ti.com/lit/ds/symlink/tpd4e001.pdf)|
|C24|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; |[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|TP6|RLDOUT|TestPoint:TestPoint_Pad_D1.5mm|RLD output bench check, before series resistance|Mechanical|
|A1|Waveshare Tiny + 2x9 socket assembly / ESP32-S3-Tiny-Kit (27070)|EMG_A4S:Waveshare_ESP32_S3_Tiny_Socket18|Waveshare SKU27069; KIT27070 includes adapter and FPC; 18 side socket contacts; bottom five omitted; 18x23.5mm body|[Manufacturer](https://files.waveshare.com/wiki/ESP32-S3-Tiny/ESP32-S3-Tiny-Sch.pdf)|
|R31|33R / RC0805FR-0733RL|Resistor_SMD:R_0805_2012Metric|33R; 1%; 0805; 0.125W; >=50V; Damping: R31-33 at Tiny, R34 at ADS1296|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R32|33R / RC0805FR-0733RL|Resistor_SMD:R_0805_2012Metric|33R; 1%; 0805; 0.125W; >=50V; Damping: R31-33 at Tiny, R34 at ADS1296|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R33|33R / RC0805FR-0733RL|Resistor_SMD:R_0805_2012Metric|33R; 1%; 0805; 0.125W; >=50V; Damping: R31-33 at Tiny, R34 at ADS1296|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R34|33R / RC0805FR-0733RL|Resistor_SMD:R_0805_2012Metric|33R; 1%; 0805; 0.125W; >=50V; Damping: R31-33 at Tiny, R34 at ADS1296|[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R35|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; |[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R36|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; |[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R37|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; |[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|R38|10k / RC0805FR-0710KL|Resistor_SMD:R_0805_2012Metric|10k; 1%; 0805; 0.125W; >=50V; |[Manufacturer](https://www.yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)|
|C26|100n / C0805C104K4RACTU|Capacitor_SMD:C_0805_2012Metric|100n; X7R 10% 16V; Carrier bypass at Tiny 3V3 output; no extra 22uF bulk|[Manufacturer](https://yageogroup.com/download/specsheet/C0805C104K4RACTU)|
|TP7|3V3_D|TestPoint:TestPoint_Pad_D1.5mm|Tiny digital supply output test pad|Mechanical|
|TP8|GND|TestPoint:TestPoint_Pad_D1.5mm|Ground test pad|Mechanical|
|H1|M3 NPTH|MountingHole:MountingHole_3.2mm_M3|3.2mm NPTH,nylon mounting hardware|Mechanical|
|H2|M3 NPTH|MountingHole:MountingHole_3.2mm_M3|3.2mm NPTH,nylon mounting hardware|Mechanical|
|H3|M3 NPTH|MountingHole:MountingHole_3.2mm_M3|3.2mm NPTH,nylon mounting hardware|Mechanical|
|H4|M3 NPTH|MountingHole:MountingHole_3.2mm_M3|3.2mm NPTH,nylon mounting hardware|Mechanical|

A1 socket assembly: 2x Harwin M20-7820942 female sockets on carrier; 2x M20-9990945 male headers on Tiny (nominal 0.64mm square; Tiny hole fit unconfirmed).
Header side-row pitch=2.54mm; row spacing=15.24mm. Always power off before insertion/removal.
Accessories: Waveshare ESP32-S3-Tiny-Kit SKU27070 (4MB/2MB) with matching USB-C adapter AND FPC; USB data cable; JST XHP-2 battery housing/contacts; six PHR-3 electrode housings and 18 contacts; PHR-2 bias housing/contacts; nylon M3 screws/spacers; solder paste,flux and magnification.
Only one kit is required; A1 is its Tiny board, and its adapter/FPC remain external to this carrier.
The 3rd contact of sensing connectors and 2nd bias contact are NC. Six pairs plus one bias =13 electrodes.
Battery input is regulated5.0-5.25V,not rawLi-ion; no charger. No galvanic isolation.
TPD4E001DBVR is the standard DBV pinout,NOT TPD4E001RDBVR. Two used channels per sensing chip; unused channels open.
Stock,landed price and physical noise performance are not confirmed by the BOM.
