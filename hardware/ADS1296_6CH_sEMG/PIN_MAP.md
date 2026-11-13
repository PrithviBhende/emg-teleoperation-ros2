# A4S physical pin/net map

## J1: REGULATED 5V IN

|Pin|Function|Net|
|---|---|---|
|1|1|BAT5V|
|2|2|GND|

## F1: 750mA PTC

|Pin|Function|Net|
|---|---|---|
|1|~|BAT5V|
|2|~|BAT_FUSED|

## SW1: BATTERY ENABLE

|Pin|Function|Net|
|---|---|---|
|2|COM|BAT_GATE|
|1|ON|GND|
|3|OFF|NC|

## Q1: AO3401A

|Pin|Function|Net|
|---|---|---|
|1|G|BAT_GATE|
|2|S|BAT_FUSED|
|3|D|BAT_SWITCHED|

## R47: 100k

|Pin|Function|Net|
|---|---|---|
|1|~|BAT_FUSED|
|2|~|BAT_GATE|

## D1: SS14

|Pin|Function|Net|
|---|---|---|
|1|~|VSYS|
|2|~|BAT_SWITCHED|

## C1: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|VSYS|
|2|~|GND|

## U2: LP5907MFX-3.3/NOPB

|Pin|Function|Net|
|---|---|---|
|1|IN|VSYS|
|3|EN|VSYS|
|2|GND|GND|
|5|OUT|AVDD|
|4|NC|NC|

## C2: 2u2

|Pin|Function|Net|
|---|---|---|
|1|~|VSYS|
|2|~|GND|

## C3: 2u2

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## TP1: AVDD

|Pin|Function|Net|
|---|---|---|
|1|TP|AVDD|

## TP2: VSYS

|Pin|Function|Net|
|---|---|---|
|1|TP|VSYS|

## C27: 1u

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C5: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C6: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C7: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C8: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C9: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C10: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C11: 1u

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## C12: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|3V3_D|
|2|~|GND|

## C13: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|3V3_D|
|2|~|GND|

## U1: ADS1296IPAG

|Pin|Function|Net|
|---|---|---|
|16|IN1P|IN1P|
|15|IN1N|IN1N|
|14|IN2P|IN2P|
|13|IN2N|IN2N|
|12|IN3P|IN3P|
|11|IN3N|IN3N|
|10|IN4P|IN4P|
|9|IN4N|IN4N|
|8|IN5P|IN5P|
|7|IN5N|IN5N|
|6|IN6P|IN6P|
|5|IN6N|IN6N|
|4|IN7P_UNUSED|AVDD|
|3|IN7N_UNUSED|AVDD|
|2|IN8P_UNUSED|AVDD|
|1|IN8N_UNUSED|AVDD|
|17|TESTP_PACE1|AVDD|
|18|TESTN_PACE2|AVDD|
|60|RLDREF|NC|
|61|RLDINV|RLDINV|
|62|RLDIN|AVDD|
|63|RLDOUT|RLDOUT|
|64|WCT|WCT|
|24|VREFP|VREFP|
|25|VREFN|GND|
|28|VCAP1|VCAP1|
|30|VCAP2|VCAP2|
|55|VCAP3|VCAP3|
|26|VCAP4|VCAP4|
|27|NC|NC|
|29|NC|NC|
|34|DIN|ADS_DIN|
|43|DOUT|ADS_DOUT|
|40|SCLK|ADS_SCLK|
|39|~{CS}|ADS_CS_N|
|47|~{DRDY}|ADS_DRDY_N|
|36|~{RESET}|ADS_RESET_N|
|35|~{PWDN}|ADS_PWDN_N|
|38|START|ADS_START|
|52|CLKSEL|ADS_CLKSEL|
|37|CLK|ADS_CLK_UNUSED|
|41|DAISY_IN|GND|
|31|RESV1|GND|
|42|GPIO1|ADS_GPIO1|
|44|GPIO2|ADS_GPIO2|
|45|GPIO3|ADS_GPIO3|
|46|GPIO4|ADS_GPIO4|
|19|AVDD|AVDD|
|21|AVDD|AVDD|
|22|AVDD|AVDD|
|54|AVDD1|AVDD|
|56|AVDD|AVDD|
|59|AVDD|AVDD|
|20|AVSS|GND|
|23|AVSS|GND|
|32|AVSS|GND|
|53|AVSS1|GND|
|57|AVSS|GND|
|58|AVSS|GND|
|48|DVDD|3V3_D|
|50|DVDD|3V3_D|
|33|DGND|GND|
|49|DGND|GND|
|51|DGND|GND|

## C14: 10u

|Pin|Function|Net|
|---|---|---|
|1|~|VREFP|
|2|~|GND|

## C15: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|VREFP|
|2|~|GND|

## C16: 22u

|Pin|Function|Net|
|---|---|---|
|1|~|VCAP1|
|2|~|GND|

## C17: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|VCAP1|
|2|~|GND|

## C18: 1u

|Pin|Function|Net|
|---|---|---|
|1|~|VCAP2|
|2|~|GND|

## C19: 1u

|Pin|Function|Net|
|---|---|---|
|1|~|VCAP3|
|2|~|GND|

## C20: 1u

|Pin|Function|Net|
|---|---|---|
|1|~|VCAP4|
|2|~|GND|

## C21: 1n

|Pin|Function|Net|
|---|---|---|
|1|~|WCT|
|2|~|GND|

## C22: 1u

|Pin|Function|Net|
|---|---|---|
|1|~|3V3_D|
|2|~|GND|

## R10: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_GPIO1|
|2|~|GND|

## R11: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_GPIO2|
|2|~|GND|

## R12: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_GPIO3|
|2|~|GND|

## R13: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_GPIO4|
|2|~|GND|

## R14: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|3V3_D|
|2|~|ADS_CLKSEL|

## R15: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_CLK_UNUSED|
|2|~|GND|

## TP3: VREFP

|Pin|Function|Net|
|---|---|---|
|1|TP|VREFP|

## TP4: VCAP1

|Pin|Function|Net|
|---|---|---|
|1|TP|VCAP1|

## TP5: ADS_DRDY_N

|Pin|Function|Net|
|---|---|---|
|1|TP|ADS_DRDY_N|

## J2: CH1: P / N / SHIELD

|Pin|Function|Net|
|---|---|---|
|1|1|E1P|
|2|2|E1N|
|3|3|NC|

## R111: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E1P|
|2|~|CLAMP1P|

## R112: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E1N|
|2|~|CLAMP1N|

## U3: TPD4E001DBVR

|Pin|Function|Net|
|---|---|---|
|1|IO1|CLAMP1P|
|6|IO4|CLAMP1N|
|5|VCC|AVDD|
|2|GND|GND|
|3|IO2_UNUSED|NC|
|4|IO3_UNUSED|NC|

## R113: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP1P|
|2|~|IN1P|

## R114: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP1N|
|2|~|IN1N|

## C111: 1n8

|Pin|Function|Net|
|---|---|---|
|1|~|IN1P|
|2|~|IN1N|

## C112: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## J3: CH2: P / N / SHIELD

|Pin|Function|Net|
|---|---|---|
|1|1|E2P|
|2|2|E2N|
|3|3|NC|

## R121: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E2P|
|2|~|CLAMP2P|

## R122: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E2N|
|2|~|CLAMP2N|

## U4: TPD4E001DBVR

|Pin|Function|Net|
|---|---|---|
|1|IO1|CLAMP2P|
|6|IO4|CLAMP2N|
|5|VCC|AVDD|
|2|GND|GND|
|3|IO2_UNUSED|NC|
|4|IO3_UNUSED|NC|

## R123: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP2P|
|2|~|IN2P|

## R124: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP2N|
|2|~|IN2N|

## C121: 1n8

|Pin|Function|Net|
|---|---|---|
|1|~|IN2P|
|2|~|IN2N|

## C122: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## J4: CH3: P / N / SHIELD

|Pin|Function|Net|
|---|---|---|
|1|1|E3P|
|2|2|E3N|
|3|3|NC|

## R131: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E3P|
|2|~|CLAMP3P|

## R132: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E3N|
|2|~|CLAMP3N|

## U5: TPD4E001DBVR

|Pin|Function|Net|
|---|---|---|
|1|IO1|CLAMP3P|
|6|IO4|CLAMP3N|
|5|VCC|AVDD|
|2|GND|GND|
|3|IO2_UNUSED|NC|
|4|IO3_UNUSED|NC|

## R133: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP3P|
|2|~|IN3P|

## R134: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP3N|
|2|~|IN3N|

## C131: 1n8

|Pin|Function|Net|
|---|---|---|
|1|~|IN3P|
|2|~|IN3N|

## C132: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## J5: CH4: P / N / SHIELD

|Pin|Function|Net|
|---|---|---|
|1|1|E4P|
|2|2|E4N|
|3|3|NC|

## R141: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E4P|
|2|~|CLAMP4P|

## R142: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E4N|
|2|~|CLAMP4N|

## U6: TPD4E001DBVR

|Pin|Function|Net|
|---|---|---|
|1|IO1|CLAMP4P|
|6|IO4|CLAMP4N|
|5|VCC|AVDD|
|2|GND|GND|
|3|IO2_UNUSED|NC|
|4|IO3_UNUSED|NC|

## R143: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP4P|
|2|~|IN4P|

## R144: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP4N|
|2|~|IN4N|

## C141: 1n8

|Pin|Function|Net|
|---|---|---|
|1|~|IN4P|
|2|~|IN4N|

## C142: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## J6: CH5: P / N / SHIELD

|Pin|Function|Net|
|---|---|---|
|1|1|E5P|
|2|2|E5N|
|3|3|NC|

## R151: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E5P|
|2|~|CLAMP5P|

## R152: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E5N|
|2|~|CLAMP5N|

## U7: TPD4E001DBVR

|Pin|Function|Net|
|---|---|---|
|1|IO1|CLAMP5P|
|6|IO4|CLAMP5N|
|5|VCC|AVDD|
|2|GND|GND|
|3|IO2_UNUSED|NC|
|4|IO3_UNUSED|NC|

## R153: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP5P|
|2|~|IN5P|

## R154: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP5N|
|2|~|IN5N|

## C151: 1n8

|Pin|Function|Net|
|---|---|---|
|1|~|IN5P|
|2|~|IN5N|

## C152: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## J7: CH6: P / N / SHIELD

|Pin|Function|Net|
|---|---|---|
|1|1|E6P|
|2|2|E6N|
|3|3|NC|

## R161: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E6P|
|2|~|CLAMP6P|

## R162: 22k

|Pin|Function|Net|
|---|---|---|
|1|~|E6N|
|2|~|CLAMP6N|

## U8: TPD4E001DBVR

|Pin|Function|Net|
|---|---|---|
|1|IO1|CLAMP6P|
|6|IO4|CLAMP6N|
|5|VCC|AVDD|
|2|GND|GND|
|3|IO2_UNUSED|NC|
|4|IO3_UNUSED|NC|

## R163: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP6P|
|2|~|IN6P|

## R164: 24k9

|Pin|Function|Net|
|---|---|---|
|1|~|CLAMP6N|
|2|~|IN6N|

## C161: 1n8

|Pin|Function|Net|
|---|---|---|
|1|~|IN6P|
|2|~|IN6N|

## C162: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## R21: 1M

|Pin|Function|Net|
|---|---|---|
|1|~|RLDOUT|
|2|~|RLDINV|

## C23: 1n5

|Pin|Function|Net|
|---|---|---|
|1|~|RLDOUT|
|2|~|RLDINV|

## R22: 110k

|Pin|Function|Net|
|---|---|---|
|1|~|RLDOUT|
|2|~|RLD_CLAMP|

## R23: 110k

|Pin|Function|Net|
|---|---|---|
|1|~|RLD_CLAMP|
|2|~|BIAS_ELECTRODE|

## J8: BIAS: 1=RLD 2=NC

|Pin|Function|Net|
|---|---|---|
|1|1|BIAS_ELECTRODE|
|2|2|NC|

## U9: TPD4E001DBVR

|Pin|Function|Net|
|---|---|---|
|1|IO1|RLD_CLAMP|
|6|IO4|NC|
|5|VCC|AVDD|
|2|GND|GND|
|3|IO2_UNUSED|NC|
|4|IO3_UNUSED|NC|

## C24: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|AVDD|
|2|~|GND|

## TP6: RLDOUT

|Pin|Function|Net|
|---|---|---|
|1|TP|RLDOUT|

## A1: Waveshare Tiny + 2x9 socket assembly

|Pin|Function|Net|
|---|---|---|
|1|SYS5V|VSYS|
|2|GND|GND|
|3|3V3_OUT|3V3_D|
|4|GPIO1|MCU_MOSI|
|5|GPIO2|MCU_CS|
|6|GPIO3|NC|
|7|GPIO4|NC|
|8|GPIO5|NC|
|9|GPIO6|NC|
|10|TX_GPIO43|NC|
|11|RX_GPIO44|NC|
|12|GPIO18|NC|
|18|GPIO12|MCU_SCLK|
|17|GPIO13|MCU_MISO|
|16|GPIO14|ADS_DRDY_N|
|15|GPIO15|ADS_START|
|14|GPIO16|ADS_PWDN_N|
|13|GPIO17|ADS_RESET_N|

## R31: 33R

|Pin|Function|Net|
|---|---|---|
|1|~|MCU_SCLK|
|2|~|ADS_SCLK|

## R32: 33R

|Pin|Function|Net|
|---|---|---|
|1|~|MCU_MOSI|
|2|~|ADS_DIN|

## R33: 33R

|Pin|Function|Net|
|---|---|---|
|1|~|MCU_CS|
|2|~|ADS_CS_N|

## R34: 33R

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_DOUT|
|2|~|MCU_MISO|

## R35: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_CS_N|
|2|~|3V3_D|

## R36: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_RESET_N|
|2|~|3V3_D|

## R37: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_PWDN_N|
|2|~|3V3_D|

## R38: 10k

|Pin|Function|Net|
|---|---|---|
|1|~|ADS_START|
|2|~|GND|

## C26: 100n

|Pin|Function|Net|
|---|---|---|
|1|~|3V3_D|
|2|~|GND|

## TP7: 3V3_D

|Pin|Function|Net|
|---|---|---|
|1|TP|3V3_D|

## TP8: GND

|Pin|Function|Net|
|---|---|---|
|1|TP|GND|

## H1: M3 NPTH

|Pin|Function|Net|
|---|---|---|

## H2: M3 NPTH

|Pin|Function|Net|
|---|---|---|

## H3: M3 NPTH

|Pin|Function|Net|
|---|---|---|

## H4: M3 NPTH

|Pin|Function|Net|
|---|---|---|

