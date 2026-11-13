import fs from 'node:fs/promises';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const outDir = 'C:/Users/prith/Documents/MYSPACE/PROJECTS/minors/hardware/ADS1296_RevA4_TinySocket_CapFix/release_review_2026-10-08';
const outPath = `${outDir}/ADS1296_RevA4_TinySocket_CapFix_BOM.xlsx`;
const wb = Workbook.create();
const bom = wb.worksheets.add('PCB BOM');
const ext = wb.worksheets.add('External items');
const font = 'Arial';

const rows = [
  ['J1','2-way power connector','B2B-XH-A(LF)(SN)','JST XH, 2.50 mm, vertical',1,7.43,1,'element14 India','https://in.element14.com/jst-japan-solderless-terminals/b2b-xh-a-lf-sn/header-vertical-2way/dp/1516276?MER=sy-me-pd-mi-acce','Through-hole','₹7.43 listing, MOQ 1; checkout/tax/delivery reconfirm.'],
  ['F1','Resettable fuse','MF-MSMF075-2','750 mA hold, 1.5 A trip, 13.2 V, 1812',1,36.31,1,'DigiKey India','https://www.digikey.in/en/products/detail/bourns-inc/MF-MSMF075-2/662843','1812 SMD','In stock shown on 2026-10-08; marked Not For New Designs by supplier.'],
  ['SW1','Slide switch','JS102011SAQN','SPDT, On-On, SMD',1,86.00,1,'DigiKey India','https://www.digikey.in/en/products/detail/c-k/JS102011SAQN/1640095','SMD','In stock shown on 2026-10-08.'],
  ['Q1','P-channel MOSFET','AO3401A','30 V, SOT-23',1,49.69,1,'DigiKey India','https://www.digikey.in/en/products/detail/alpha-omega-semiconductor-inc/AO3401A/1855773','SOT-23','Quote is for AOS manufacturer part.'],
  ['R47','Resistor','RC0805FR-07100KL','100 kΩ, 1%, 0805',1,9.32,1,'Mouser India','https://www.mouser.in/en/ProductDetail/YAGEO/RC0805FR-07100KL?qs=8Y8p%252BasKcI7rEWn6FcVdAA%3D%3D','0805','Observed supplier listing; reconfirm price, tax and stock.'],
  ['D1','Schottky diode','SS14 (onsemi)','40 V, 1 A, SMA / DO-214AC',1,42.04,1,'DigiKey India','https://www.digikey.in/en/products/detail/onsemi/SS14/965474','SMA','Use SMA package; SS14W in SOD-123 is not footprint-compatible.'],
  ['C1, C5-C10, C12-C13, C15, C17, C24, C26, C112, C122, C132, C142, C152, C162','Ceramic capacitor','C0805C104K4RACTU','100 nF, 16 V, X7R, 10%, 0805',19,5.57,10,'Mouser India','https://www.mouser.in/ProductDetail/KEMET/C0805C104K4RACTU?qs=Pc30aiB8zWWfqQNJWggt%252BA%3D%3D','0805','Historical observed quantity-tier price; live stock/price needs reconfirmation.'],
  ['U2','Low-noise LDO regulator','LP5907MFX-3.3/NOPB','3.3 V fixed, 250 mA, SOT-23-5',1,17.11,1,'Evelta','https://evelta.com/texas-instruments-lp5907mfx-3-3-nopb-fixed-ldo-voltage-regulator-3-3vout/','SOT-23-5','₹17.11 incl. GST shown; supplier authorization not established; reconfirm.'],
  ['C2-C3','Ceramic capacitor','C0805C225K4RACTU','2.2 µF, 16 V, X7R, 10%, 0805',2,37.70,1,'LionCircuits','https://www.lioncircuits.com/parts/C0805C225K4RACTU','0805','Observed listing; reconfirm live price, stock and delivery at checkout.'],
  ['C11, C18-C20, C22, C27','Ceramic capacitor','C0805C105K4RACTU','1 µF, 16 V, X7R, 10%, 0805',6,8.39,10,'Mouser India','https://www.mouser.in/ProductDetail/KEMET/C0805C105K4RACTU?qs=yrVqjCObULOefkidH6lLLQ%3D%3D','0805','Mouser listing showed ₹8.39 each at quantity 10 and stock on 2026-10-08; delivery/tax at checkout.'],
  ['U1','Six-channel biopotential ADC','ADS1296IPAG','24-bit, 6-channel, TQFP-64',1,4429.78,1,'Mouser India','https://www.mouser.in/en/ProductDetail/Texas-Instruments/ADS1296IPAG?qs=sGAEpiMZZMtgJDuTUz7Xu9XaB9kOWLvLwc8sBR0S0tA%3D','TQFP-64, 0.5 mm pitch','Candidate price only; listing/stock/landed costs need checkout reconfirmation. TI direct showed out of stock.'],
  ['C14','Ceramic capacitor','C1206C106K4PACTU','10 µF, 16 V, X5R, 10%, 1206',1,51.60,1,'DigiKey India','https://www.digikey.in/en/products/detail/kemet/C1206C106K4PACTU/1465625','1206','DigiKey listing showed ₹51.60 each and stock on 2026-10-08; import/tax/shipping extra per checkout.'],
  ['C16','Ceramic capacitor','C1210C226K4PACTU','22 µF, 16 V, X5R, 10%, 1210',1,83.13,1,'DigiKey India','https://www.digikey.in/en/products/detail/kemet/C1210C226K4PACTU/1465626','1210','Observed listing; reconfirm current price, import/tax and shipping at checkout.'],
  ['C21','Ceramic capacitor','C0805C102J5GACTU','1 nF, 50 V, C0G, 5%, 0805',1,16.24,1,'DigiKey India','https://www.digikey.in/en/products/detail/kemet/C0805C102J5GACTU/411135','0805','DigiKey listing showed ₹16.24 each and stock on 2026-10-08; import/tax/shipping extra per checkout.'],
  ['R10-R15, R35-R38','Resistor','RC0805FR-0710KL','10 kΩ, 1%, 0805',10,1.2744,10,'Evelta','https://evelta.com/10k-1-0-125w-0805-chip-resistor/','0805','₹1.08 ex-GST each at qty 10; ₹1.2744 incl. 18% GST estimate; shipping extra.'],
  ['J2-J7','3-way electrode connector','B3B-PH-K-S(LF)(SN)','JST PH, 2.00 mm, vertical',6,15.29,1,'DigiKey India','https://www.digikey.in/en/products/detail/jst-sales-america-inc/B3B-PH-K-S/926612','Through-hole','Unit listing observed; checkout/tax/shipping reconfirm.'],
  ['R111, R121, R131, R141, R151, R161, R112, R122, R132, R142, R152, R162','Precision resistor','RT0805BRD0722KL','22 kΩ, 0.1%, ≤25 ppm/K, 0805',12,7.931,10,'DigiKey India','https://www.digikey.in/en/products/detail/yageo/RT0805BRD0722KL/5139281','0805','Quantity-10 tier; 12 required. ₹7.931/unit observed; tax/shipping treatment to confirm.'],
  ['U3-U8, U9','ESD protection array','TPD4E001DBVR','4-line low-capacitance ESD, standard DBV pinout',7,64.01,1,'Mouser India','https://www.mouser.in/en/ProductDetail/Texas-Instruments/TPD4E001DBVR?qs=TeC8nwD7mVpPZhmkNxkg4A%3D%3D','SOT-23-6','BLOCKED: checked stock 0; incoming shown in 2027. Do not treat as buyable for the deadline. Alternative not approved.'],
  ['R113, R123, R133, R143, R153, R163, R114, R124, R134, R144, R154, R164','Precision resistor','RT0805BRD0724K9L','24.9 kΩ, 0.1%, ≤25 ppm/K, 0805',12,7.931,10,'DigiKey India','https://www.digikey.in/en/products/detail/yageo/RT0805BRD0724K9L/1075743','0805','Quantity-10 tier; 12 required. ₹7.931/unit observed; tax/shipping treatment to confirm.'],
  ['C111, C121, C131, C141, C151, C161','Ceramic capacitor','C0805C182J5GACTU','1.8 nF, 50 V, C0G, 5%, 0805',6,15.621,10,'LionCircuits','https://www.lioncircuits.com/','0805','Fresh listing: 10-piece tier ₹15.621 each; buy quantity 10 minimum (₹156.21 listing subtotal); delivery estimate 7-10 days, not arrival guarantee.'],
  ['R21','Resistor','RC0805FR-071ML','1 MΩ, 1%, 0805',1,1.30,1,'Evelta','https://evelta.com/1m-1-0-125w-0805-chip-resistor/','0805','₹1.10 ex-GST / ₹1.30 incl. GST observed; shipping extra.'],
  ['C23','Ceramic capacitor','C0805C152J5GACTU','1.5 nF, 50 V, C0G, 5%, 0805',1,15.29,1,'DigiKey India','https://www.digikey.in/en/products/detail/kemet/C0805C152J5GACTU/2211962','0805','DigiKey listing showed ₹15.29 each and stock on 2026-10-08; import/tax/shipping extra per checkout.'],
  ['R22-R23','Resistor','RC0805FR-07110KL','110 kΩ, 1%, 0805',2,1.298,1,'Evelta','https://evelta.com/110k-1-0-125w-0805-chip-resistor/','0805','₹1.10 ex-GST each; ₹1.298 incl. 18% GST estimate; shipping extra.'],
  ['J8','2-way bias connector','B2B-PH-K-S(LF)(SN)','JST PH, 2.00 mm, vertical',1,11.47,1,'DigiKey India','https://www.digikey.in/en/products/detail/jst-sales-america-inc/B2B-PH-K-S/926611','Through-hole','Unit listing observed; confirm current stock/tax at checkout.'],
  ['A1','MCU development module + adapter kit','ESP32-S3-Tiny-Kit, Waveshare SKU 27070','ESP32-S3-Tiny + USB-C adapter + FPC',1,635,1,'Hubtronics','https://hubtronics.in/esp32-s3-tiny-kit','Socket kit / assembled module','₹635 incl. GST shown. Carrier socket fit and delivery to PIN 576104 remain unconfirmed.'],
  ['R31-R34','Resistor','RC0805FR-0733RL','33 Ω, 1%, 0805',4,2.36,1,'Evelta','https://evelta.com/33r-1-0-125w-0805-chip-resistor/','0805','₹2 ex-GST each; ₹2.36 incl. 18% GST estimate; shipping extra.'],
];

const headers = ['Ref(s)','Component','Exact manufacturer part / SKU','Value / rating','PCB qty','Min quote qty','Observed unit price (₹)','Indicative buy amount (₹)','Quote status','Supplier','Price/source link','Package / footprint','Ordering notes'];
bom.showGridLines = false;
bom.getRange('A1').values = [['ADS1296 RevA4 TinySocket CapFix | Purchase BOM']];
bom.getRange('A2').values = [['Grouped by exact part number. Prices are observed listings, not a delivered quote. Blank amounts mean no dependable price was captured. Confirm stock, tax, shipping and PIN 576104 before ordering.']];
bom.getRange('A3').values = [['Note: 26 purchase groups cover 101 fitted components. TP1–TP8 are bare copper pads and H1–H4 are unplated holes, not purchased components. Amounts are estimates, not a landed total. TPD4E001 is out of stock.']];
bom.getRange('A5:M5').values = [headers];
const body = rows.map((r)=>[r[0],r[1],r[2],r[3],r[4],r[6],r[5],null,r[10].startsWith('BLOCKED')?'Unavailable at checked suppliers':r[10].startsWith('Fresh listing')?'Observed; delivery unconfirmed':'Listing observed; reconfirm',r[7],r[8],r[9],r[10]]);
bom.getRange(`A6:M${5+body.length}`).values = body;
for(let i=0;i<body.length;i++){const row=6+i;bom.getRange(`H${row}`).formulas=[[`=IF(G${row}="","",ROUND(MAX(E${row},F${row})*G${row},2))`]];}
bom.getRange(`A${6+body.length}`).values=[['Indicative extension of priced rows only (mixed tax basis; excludes shipping, PCB, isolation and unpriced items)']];
bom.getRange(`H${6+body.length}`).formulas=[[`=ROUND(SUM(H6:H${5+body.length}),2)`]];
bom.getRange(`A1:M${6+body.length}`).format.font={name:font,size:10,color:'#263238'};
bom.getRange('A1:M1').format.font={name:font,size:14,bold:true,color:'#17365D'};
bom.getRange('A2:M3').format.font={name:font,size:9,italic:true,color:'#555555'};
bom.getRange('A5:M5').format={fill:'#24476B',font:{name:font,size:10,bold:true,color:'#FFFFFF'},wrapText:true,verticalAlignment:'center',horizontalAlignment:'center'};
bom.getRange(`A6:M${5+body.length}`).format.verticalAlignment='center';
bom.getRange(`G6:H${5+body.length}`).setNumberFormat('₹#,##0.00');
bom.getRange(`E6:F${5+body.length}`).format.numberFormat='#,##0';
bom.getRange(`A6:M${5+body.length}`).format.wrapText=true;
bom.getRange(`A${6+body.length}:M${6+body.length}`).format={fill:'#E8EEF4',font:{name:font,bold:true,color:'#17365D'},borders:{top:{style:'thin',color:'#24476B'}}};
bom.getRange(`H6:H${5+body.length}`).setNumberFormat('₹#,##0.00');
bom.getRange('A:A').format.columnWidth=24;bom.getRange('B:B').format.columnWidth=24;bom.getRange('C:C').format.columnWidth=31;bom.getRange('D:D').format.columnWidth=34;bom.getRange('E:F').format.columnWidth=12;bom.getRange('G:H').format.columnWidth=18;bom.getRange('I:I').format.columnWidth=23;bom.getRange('J:J').format.columnWidth=17;bom.getRange('K:K').format.columnWidth=54;bom.getRange('L:L').format.columnWidth=22;bom.getRange('M:M').format.columnWidth=62;
bom.getRange('A2:M3').format.rowHeight=30;bom.getRange('A5:M5').format.rowHeight=36;bom.getRange(`A6:M${5+body.length}`).format.rowHeight=42;
bom.freezePanes.freezeRows(5);bom.freezePanes.freezeColumns(2);
bom.tables.add(`A5:M${5+body.length}`,true,'PCB_BOM');

const extRows=[
 ['MCU kit','Waveshare ESP32-S3-Tiny-Kit SKU27070','1','Included as A1 in PCB BOM','Included','USB-C adapter and matching FPC are in kit listing; confirm delivery.','https://hubtronics.in/esp32-s3-tiny-kit'],
 ['Female socket headers','Harwin M20-7820942, 1x9','2','Separate from MCU kit','₹178.68 each observed','DigiKey India listing; check delivery and dimensional fit.','https://www.digikey.in/en/products/detail/harwin-inc/M20-7820942/3919444'],
 ['Male headers','Harwin M20-9990945, 1x9','2','Separate from MCU kit','₹38.20 each observed listing','Confirm exact geometry and stock at checkout.','https://www.mouser.in/en/ProductDetail/Harwin/M20-9990945?qs=ulE8k0yEMYbS6Ii%2FrXEOUQ%3D%3D'],
 ['PHR-3 wire housings','JST PHR-3','6 required; listing tier 10','External electrode harness','₹5.12 each at qty 10 listing tier','Six channel connectors; pin 3 is NC on carrier. Confirm final price and stock.','https://www.mouser.in/en/ProductDetail/JST-Commercial/PHR-3?qs=uQD7XCvsSCM92rt8vZZnwg%3D%3D'],
 ['PHR-2 wire housing','JST PHR-2','1','External bias harness','₹9.56 each observed','Second position is NC on carrier. Confirm current stock and checkout.','https://www.digikey.in/en/products/detail/jst-sales-america-inc/PHR-2/608607'],
 ['Crimp contacts','JST SPH002T-P0.5S','13 wired positions; buy extras as desired','External harness','Price/stock to reconfirm','Confirm wire gauge and crimp tooling. NC positions may remain empty.',''],
 ['Power housing','JST XHP-2','1','Battery/source lead','Price/stock to reconfirm','Carrier input requires regulated 5.0–5.25 V, not a raw Li-ion cell.',''],
 ['Power crimp contacts','JST SXH001T-P0.6','2','Power lead','Price/stock to reconfirm','Match contact to the XH series housing and wire size.',''],
 ['Surface EMG electrodes','Ag/AgCl snap electrodes','13 per complete setup','Electrode consumable','Price/size unverified','Match snap stud size to the selected lead; quantity includes six differential pairs plus one bias electrode.',''],
 ['Electrode leads','Snap-to-wire leads','13','Electrode harness','Price/size unverified','Match connector, snap stud and cable length; strain relief and short twisted pairs recommended.',''],
 ['USB cable','USB data cable for Tiny adapter','1','Data/power cable','Price unverified','Ensure data-capable cable. USB alone does not provide galvanic isolation.',''],
 ['Mounting hardware','M3 nylon screw/spacer set','4 sets','Mechanical assembly','Price unverified','Board has four non-plated mounting holes.',''],
 ['Regulated supply','5.0–5.25 V regulated source','1','Optional external power source','Price unverified','Never connect raw Li-ion voltage to J1; do not use a charger for human-connected recording.',''],
 ['Isolation interface','Reviewed isolated wired data and power link','1','Required for selected wired PC capture route','Not selected / not priced','Must review the whole electrode, power and USB path; a data-only isolator is insufficient.',''],
 ['Assembly consumables','Flux, solder paste/wire, wick, magnification','As needed','Assembly','Not priced','ADS1296 TQFP-64 has 0.5 mm pitch; plan careful SMD assembly.',''],
];
ext.showGridLines=false;
ext.getRange('A1').values=[['External accessories and unresolved purchase items']];
ext.getRange('A2').values=[['These items are not all fitted to the PCB. Prices are left unfilled where a reliable current quote was not captured.']];
ext.getRange('A4:G4').values=[['Item','Exact part / specification','Qty needed','Use','Observed price/status','Fit or ordering note','Source link']];
ext.getRange(`A5:G${4+extRows.length}`).values=extRows;
ext.getRange(`A1:G${4+extRows.length}`).format.font={name:font,size:10,color:'#263238'};
ext.getRange('A1:G1').format.font={name:font,size:14,bold:true,color:'#17365D'};
ext.getRange('A2:G2').format.font={name:font,size:9,italic:true,color:'#555555'};
ext.getRange('A4:G4').format={fill:'#24476B',font:{name:font,size:10,bold:true,color:'#FFFFFF'},wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};
ext.getRange(`A5:G${4+extRows.length}`).format={wrapText:true,verticalAlignment:'center'};
ext.getRange('A:A').format.columnWidth=25;ext.getRange('B:B').format.columnWidth=40;ext.getRange('C:C').format.columnWidth=25;ext.getRange('D:D').format.columnWidth=28;ext.getRange('E:E').format.columnWidth=30;ext.getRange('F:F').format.columnWidth=65;ext.getRange('G:G').format.columnWidth=60;
ext.getRange('A2:G2').format.rowHeight=30;ext.getRange('A4:G4').format.rowHeight=34;ext.getRange(`A5:G${4+extRows.length}`).format.rowHeight=42;
ext.freezePanes.freezeRows(4);ext.tables.add(`A4:G${4+extRows.length}`,true,'External_Items');

wb.recalculate();
const peek=await wb.inspect({kind:'table',sheetId:'PCB BOM',range:`A5:M${6+body.length}`,include:'values,formulas',tableMaxRows:40,tableMaxCols:13,maxChars:15000});
console.log(peek.ndjson);
const preview=await wb.render({sheetName:'PCB BOM',range:'A1:M12',scale:1,format:'png'});
await fs.writeFile(`${outDir}/bom_preview.png`,new Uint8Array(await preview.arrayBuffer()));
const preview2=await wb.render({sheetName:'External items',autoCrop:'all',scale:1,format:'png'});
await fs.writeFile(`${outDir}/external_items_preview.png`,new Uint8Array(await preview2.arrayBuffer()));
const xlsx=await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(outPath);
console.log(`SAVED ${outPath}`);
