"""Draw explanatory wiring pictures from the freshly exported KiCad netlist."""
from pathlib import Path
import xml.etree.ElementTree as ET
import html, json, hashlib

ROOT = Path(__file__).resolve().parent
source = ROOT / 'source_netlist.xml'
tree = ET.parse(source).getroot()
parts = {c.attrib['ref']: c.findtext('value') for c in tree.findall('./components/comp')}
nets = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name']
        for net in tree.findall('./nets/net') for n in net.findall('node')}
checks = []
def net(ref, pin): return nets.get((ref, str(pin)))
def same(*terminals):
    names = [net(r, p) for r, p in terminals]
    assert None not in names and len(set(names)) == 1, (terminals, names)
    checks.append({'terminals': terminals, 'net': names[0]})
def component(ref, value):
    assert parts[ref] == value, (ref, parts[ref], value)
def value(ref):
    return {'22k':'22 kΩ', '24k9':'24.9 kΩ', '33R':'33 Ω', '100n':'100 nF',
            '1n8':'1.8 nF', '1n5':'1.5 nF','1u':'1 µF','10u':'10 µF',
            '22u':'22 µF','2u2':'2.2 µF','1n':'1 nF','1M':'1 MΩ',
            '110k':'110 kΩ','10k':'10 kΩ','100k':'100 kΩ'}.get(parts[ref],parts[ref])

INK='#172d41'; MUTED='#526778'; BLUE='#2177ae'; GREEN='#178064'; RED='#b94542'; PURPLE='#7555a4'
class Drawing:
    def __init__(self, title, subtitle, height=1660):
        self.h=height
        self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="{height}" viewBox="0 0 2400 {height}">',
            '<rect width="100%" height="100%" fill="#f3f6f9"/>',
            '<style>text{font-family:Segoe UI,Arial,sans-serif}path,line,rect{stroke-linejoin:round;stroke-linecap:round}</style>']
        self.text(55,65,title,40,bold=True)
        self.text(55,108,subtitle,23,MUTED)
    def text(self,x,y,t,size=22,color=INK,bold=False,anchor='start'):
        self.s.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{html.escape(str(t))}</text>')
    def box(self,x,y,w,h,fill='white',stroke='#d3dde5',radius=15):
        self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    def panel(self,x,y,w,h,title):
        self.box(x,y,w,h);self.text(x+25,y+40,title,27,bold=True)
    def wire(self,pts,color=BLUE,width=3):
        self.s.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{color}" stroke-width="{width}"/>')
    def dot(self,x,y,color=BLUE):
        self.s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{color}"/>')
    def resistor(self,x,y,ref,w=115,color=BLUE):
        self.wire([(x,y),(x+15,y)],color)
        self.box(x+15,y-13,w-30,26,'#fff1d4','#af8740',3)
        self.wire([(x+w-15,y),(x+w,y)],color)
        self.text(x+w/2,y-24,f'{ref} · {value(ref)}',18,INK,anchor='middle')
    def cap(self,x,y1,y2,label,color=GREEN):
        cy=(y1+y2)/2
        self.wire([(x,y1),(x,cy-7)],color)
        self.wire([(x-15,cy-7),(x+15,cy-7)],color)
        self.wire([(x-15,cy+7),(x+15,cy+7)],color)
        self.wire([(x,cy+7),(x,y2)],color)
        self.text(x+23,cy+6,label,19)
        self.dot(x,y1,color);self.dot(x,y2,color)
    def ground(self,x,y):
        self.wire([(x,y),(x,y+12)],MUTED)
        for dy,w in [(12,15),(19,10),(26,5)]:self.wire([(x-w,y+dy),(x+w,y+dy)],MUTED,2)
    def footer(self,t):
        self.text(55,self.h-55,t,21,MUTED)
        self.text(55,self.h-23,'ADS1296 A4 TinySocket CapFix • electrical connections from the saved KiCad schematic • drawn pin positions are rearranged for clarity',19,MUTED)
    def save(self,name):
        (ROOT/(name+'.svg')).write_text('\n'.join(self.s+['</svg>']),encoding='utf-8')

# 01: all six input pairs and all eight MCU signals.
d=Drawing('How the electrodes connect to the computer',
          'Start at the left. Each channel has a + and − electrode wire; the ADS1296 converts them to digital readings.',1750)
d.panel(40,145,850,1235,'1  Electrode inputs and RC filters')
d.box(1020,210,325,1100,'#e8f1f8','#7a9caf')
d.text(1182,190,'U1 · ADS1296',30,bold=True,anchor='middle')
d.text(1182,1340,'6 simultaneous channels',20,MUTED,anchor='middle')
d.text(1182,1369,'4,000 samples/s / channel',20,MUTED,anchor='middle')
d.box(1925,305,430,955,'#e8f4ee','#71a288')
d.text(2140,356,'A1 · Waveshare',29,bold=True,anchor='middle')
d.text(2140,393,'ESP32-S3-Tiny',29,bold=True,anchor='middle')
d.text(2140,430,'Removable socket assembly',21,MUTED,anchor='middle')
for ch in range(1,7):
    j=f'J{ch+1}'; r1=f'R1{ch}1';r2=f'R1{ch}2';r3=f'R1{ch}3';r4=f'R1{ch}4';c=f'C1{ch}1';u=f'U{ch+2}'
    yp=285+(ch-1)*177;yn=yp+67; pp=18-2*ch;pn=pp-1
    d.text(70,yp-57,f'CH{ch}  /  {j}',24,bold=True)
    for y,jpin,ra,rb,adc,pol,upin in [(yp,1,r1,r3,pp,'+',1),(yn,2,r2,r4,pn,'−',6)]:
        same((j,jpin),(ra,1));same((ra,2),(rb,1),(u,upin));same((rb,2),('U1',adc),(c,1 if pol=='+' else 2))
        d.text(70,y+7,f'pin {jpin}  {pol}',20)
        d.wire([(175,y),(225,y)]);d.resistor(225,y,ra)
        d.wire([(340,y),(485,y)]);d.dot(412,y)
        d.resistor(485,y,rb);d.wire([(600,y),(1020,y)])
        d.text(1040,y+7,f'{adc}  IN{ch}{"P" if pol=="+" else "N"}',21)
    d.cap(720,yp,yn,f'{c}  {value(c)}')
    d.text(350,yn+37,f'{u} protection connects at the dots → picture 03',18,MUTED)
    d.text(70,yn+25,'pin 3: NC',18,MUTED)
d.text(1460,245,'2  Digital wires (SPI + control)',28,bold=True)
spi=[('CS_N',39,5,'GPIO2','R33'),('SCLK',40,18,'GPIO12','R31'),
     ('DIN / MOSI',34,4,'GPIO1','R32'),('DOUT / MISO',43,17,'GPIO13','R34'),
     ('DRDY_N',47,16,'GPIO14',None),('START',38,15,'GPIO15',None),
     ('PWDN_N',35,14,'GPIO16',None),('RESET_N',36,13,'GPIO17',None)]
for i,(sig,up,ap,gpio,r) in enumerate(spi):
    y=500+i*92
    d.text(1322,y-13,f'{up}  {sig}',19,anchor='end')
    d.text(1945,y+7,f'socket {ap}  /  {gpio}',22)
    if r:
        leftpin=1 if r=='R34' else 2;rightpin=3-leftpin
        same(('U1',up),(r,leftpin));same(('A1',ap),(r,rightpin));component(r,'33R')
        d.wire([(1345,y),(1530,y)],PURPLE);d.resistor(1530,y,r,140,PURPLE);d.wire([(1670,y),(1925,y)],PURPLE)
    else:
        same(('U1',up),('A1',ap));d.wire([(1345,y),(1925,y)],PURPLE)
d.text(1410,1285,'_N means the signal is active when LOW.',19,MUTED)
d.panel(40,1410,2315,245,'3  Power, bias and USB connections')
d.text(70,1500,'J1: regulated 5 V → power circuit → VSYS → A1 socket 1',24,RED)
d.text(70,1544,'LP5907 (U2) → analog 3.3 V (AVDD) → ADS1296 + protection ICs',24,RED)
d.text(70,1588,'A1 socket 3 → digital 3.3 V (3V3_D) → ADS1296 digital supply',24,RED)
d.text(1395,1500,'Tiny FPC → kit USB-C adapter → PC / ML',25,bold=True)
d.text(1395,1544,'J8 pin 1 ← RLD bias circuit (picture 03)',24,GREEN)
d.text(1395,1588,'Power, pull resistors and capacitors: picture 02',22,MUTED)
d.footer('Filled dots are connections. Matching net names also connect. NC = leave unconnected. Protection branch details are expanded in picture 03.')
d.save('01_main_connections')

# 02: actual supply circuit and the grouped parallel bypass branches.
d=Drawing('Power supplies, bypass capacitors and control pins',
          'Red = supply rail. Gray = GND return. Capacitors shown in the same group connect in parallel.',2220)
d.panel(40,145,2315,565,'1  Regulated 5 V input, switch and analog regulator')
d.text(80,240,'J1 pin 1',24,bold=True);d.text(80,275,'regulated 5 V',20,RED)
d.wire([(210,245),(265,245)],RED);d.resistor(265,245,'F1',150,RED)
d.wire([(415,245),(600,245)],RED);d.dot(500,245,RED)
d.box(600,205,270,120,'#fff3e8','#cb9a72');d.text(735,238,'Q1  AO3401A',23,bold=True,anchor='middle')
d.text(620,280,'2  S',21);d.text(850,280,'3  D',21,anchor='end');d.text(735,312,'1  G',21,anchor='middle')
d.wire([(870,245),(965,245)],RED)
d.box(965,220,185,50,'#fff1d4','#af8740',5);d.text(1057,253,'D1  SS14',22,anchor='middle')
d.text(970,207,'2  anode',18);d.text(1145,207,'1  cathode',18,anchor='end')
d.wire([(1150,245),(1440,245)],RED);d.dot(1260,245,RED);d.text(1250,216,'VSYS',23,RED,bold=True)
d.box(1440,200,310,220,'#fbece9','#c38e89');d.text(1595,238,'U2  LP5907',26,bold=True,anchor='middle')
d.text(1460,279,'1 IN + 3 EN',21);d.text(1730,279,'5 OUT',21,anchor='end')
d.text(1460,360,'2 GND',21);d.text(1460,394,'4 NC',21)
d.wire([(1750,245),(2270,245)],RED);d.text(1955,216,'AVDD · analog 3.3 V',25,RED,bold=True)
d.cap(1990,245,375,'C3  2.2 µF',RED);d.ground(1990,375)
d.wire([(1450,347),(1370,347),(1370,460)],MUTED);d.ground(1370,460)
d.wire([(500,245),(500,400),(570,400)],RED);d.resistor(570,400,'R47',135,RED)
d.wire([(705,400),(735,400),(735,325)],MUTED);d.dot(735,400,MUTED)
d.wire([(735,400),(735,550),(920,550)],MUTED)
d.box(920,505,300,130,'#edf1f4','#aebdca');d.text(1070,535,'SW1 · battery enable',23,bold=True,anchor='middle')
d.text(940,570,'2 COM → 1 ON → GND',20);d.text(940,605,'3 OFF: unconnected',20);d.ground(1245,550);d.wire([(1220,550),(1245,550)],MUTED)
d.text(80,610,'J1 pin 2 → GND',24,MUTED)
d.text(1470,505,'VSYS → A1 socket 1 (SYS5V)',23,RED)
d.text(1470,545,'A1 socket 2 → GND',23,MUTED)
d.text(1470,585,'A1 socket 3 → 3V3_D (digital 3.3 V output)',23,RED)
d.text(1470,630,'USB power reaches the Tiny through its kit adapter.',20,MUTED)
for terms in [[('J1',1),('F1',1)],[('F1',2),('Q1',2),('R47',1)], [('Q1',1),('R47',2),('SW1',2)], [('Q1',3),('D1',2)], [('D1',1),('U2',1),('U2',3),('A1',1)], [('U2',5),('C3',1)], [('J1',2),('SW1',1),('U2',2),('A1',2)]]:same(*terms)

def bank(x,y,w,title,left,right,refs):
    d.box(x,y,w,132,'#f8fafc','#d9e1e8',9)
    d.text(x+16,y+27,title,21,bold=True)
    d.text(x+16,y+62,left,19,RED)
    d.text(x+w-16,y+62,right,19,MUTED,anchor='end')
    d.wire([(x+25,y+88),(x+130,y+88)],RED)
    d.box(x+130,y+72,w-255,35,'#fff5df','#d0b57a',4)
    d.text(x+130+(w-255)/2,y+96,'  ∥  '.join(f'{r} {value(r)}' for r in refs),18,anchor='middle')
    d.wire([(x+w-125,y+88),(x+w-25,y+88)],MUTED)
    for r in refs: same((r,2),('U2',2))

d.panel(40,745,1135,605,'2  Supply capacitors: each branch goes to GND')
bank(65,815,1085,'VSYS input bypass','VSYS','GND',['C1','C2'])
bank(65,958,1085,'Analog rail local bypass','AVDD','GND',['C5','C6','C7','C8','C9','C10'])
bank(65,1101,1085,'Analog bulk + pin 54 local branch','AVDD','GND',['C11','C27'])
d.text(80,1290,'C3 is drawn at U2 above. Each protection IC also has 100 nF.',20,MUTED)
d.panel(1210,745,1145,605,'3  Internal reference and internal regulator capacitors')
rows=[('24  VREFP',['C14','C15'],24),('28  VCAP1',['C16','C17'],28),('30  VCAP2',['C18'],30),('55  VCAP3',['C19'],55),('26  VCAP4',['C20'],26),('64  WCT',['C21'],64)]
for i,(label,refs,pin) in enumerate(rows):
    y=840+i*78
    d.text(1240,y+7,f'U1 pin {label}',21)
    d.wire([(1485,y),(1600,y)],GREEN)
    d.box(1600,y-23,535,46,'#fff5df','#d0b57a',5)
    d.text(1867,y+7,'  ∥  '.join(f'{r} {value(r)}' for r in refs),21,anchor='middle')
    d.wire([(2135,y),(2250,y)],MUTED);d.ground(2250,y)
    for r in refs:same(('U1',pin),(r,1))
d.text(1240,1320,'U1 pin 25 (VREFN) → GND. ∥ means parallel components.',20,MUTED)
d.panel(40,1385,1135,690,'4  ADS1296 supply pins and digital bypass')
d.text(75,1470,'AVDD → U1 pins 19, 21, 22, 54, 56, 59',25,RED,bold=True)
d.text(75,1520,'3V3_D → U1 pins 48, 50',25,RED,bold=True)
d.text(75,1570,'GND → U1 pins 20, 23, 25, 32, 33, 49, 51, 53, 57, 58',22,MUTED)
bank(65,1610,1085,'Digital rail bypass','3V3_D','GND',['C12','C13','C22','C26'])
d.text(75,1800,'Other fixed U1 connections',25,bold=True)
d.text(75,1850,'AVDD → pins 1, 2, 3, 4, 17, 18, 62',23,RED)
d.text(75,1895,'GND → pins 31 and 41',23,MUTED)
d.text(75,1940,'NC → pins 27, 29 and 60',23,MUTED)
d.text(75,2000,'Pin 60 uses the internal RLD reference in this design.',20,MUTED)
d.panel(1210,1385,1145,690,'5  Pull resistors and fixed logic settings')
pulls=[(39,'R35','3V3_D'),(36,'R36','3V3_D'),(35,'R37','3V3_D'),(38,'R38','GND'),(52,'R14','3V3_D'),(37,'R15','GND'),(42,'R10','GND'),(44,'R11','GND'),(45,'R12','GND'),(46,'R13','GND')]
for i,(pin,r,rail) in enumerate(pulls):
    y=1470+i*53
    d.text(1245,y+7,f'U1 pin {pin}',22)
    d.wire([(1420,y),(1530,y)],PURPLE);d.resistor(1530,y,r,190,PURPLE);d.wire([(1720,y),(1880,y)],PURPLE)
    d.text(1900,y+7,rail,22,RED if rail=='3V3_D' else MUTED)
    terminal=2 if r=='R14' else 1
    same(('U1',pin),(r,terminal))
    same((r,3-terminal),('A1',3 if rail=='3V3_D' else 2))
for rail,pins in [('AVDD',[1,2,3,4,17,18,19,21,22,54,56,59,62]),('3V3_D',[48,50]),('GND',[20,23,25,31,32,33,41,49,51,53,57,58])]:
    for p in pins:assert net('U1',p)==rail
for refs,rail in [(['C1','C2'],'VSYS'),(['C3','C5','C6','C7','C8','C9','C10','C11','C27'],'AVDD'),(['C12','C13','C22','C26'],'3V3_D')]:
    for r in refs:assert net(r,1)==rail
d.footer('Supply capacitors are parallel branches between a rail and GND. The two 3.3 V rails are separate named nets. This is an explanatory wiring view.')
d.save('02_power_and_capacitors')

# 03: expand protection branches and feedback so there are no hidden signal blocks.
d=Drawing('Input protection and the separate bias electrode',
          'The protection chip taps both electrode wires. The bias output uses a separate electrode through J8.',1930)
d.panel(40,145,2315,655,'1  One complete electrode input (CH1 shown; the table below identifies CH2–CH6 parts)')
for y,jp,ra,rb,up,cp in [(285,1,'R111','R113',16,1),(555,2,'R112','R114',15,6)]:
    d.text(80,y+7,f'J2 pin {jp}',23,bold=True);d.wire([(220,y),(340,y)])
    d.resistor(340,y,ra,160);d.wire([(500,y),(1380,y)]);d.dot(730,y)
    d.resistor(1380,y,rb,180);d.wire([(1560,y),(2160,y)])
    d.text(2190,y+7,f'U1 pin {up}',22,bold=True)
d.box(655,360,440,125,'#e8f4ee','#71a288')
d.text(875,400,'U3 · TPD4E001',26,bold=True,anchor='middle')
d.text(685,437,'pin 1 IO1',21);d.text(685,470,'pin 6 IO4',21)
d.wire([(730,285),(730,360)]);d.wire([(730,485),(730,555)])
d.text(1120,403,'pin 5 VCC → AVDD',22,RED)
d.text(1120,447,'pin 2 GND → GND',22,MUTED)
d.text(1120,487,'pins 3 + 4 → NC',21,MUTED)
d.cap(1850,285,555,'C111  1.8 nF')
d.text(80,660,'J2 pin 3: NC',23,MUTED)
d.text(80,712,'C112 100 nF: U3 pin 5 (AVDD) → capacitor → U3 pin 2 (GND)',24)
d.text(80,757,'The differential capacitor bridges IN1P and IN1N. It does not connect to GND.',22,MUTED)
d.panel(40,830,2315,405,'2  Repeat the same circuit for all six channels')
headers=[(75,'Channel / jack'),(380,'22 kΩ pair'),(730,'Protection IC'),(1080,'24.9 kΩ pair'),(1450,'1.8 nF bridge'),(1820,'100 nF bypass'),(2150,'U1 P / N')]
for x,t in headers:d.text(x,920,t,21,bold=True)
for ch in range(1,7):
    y=960+(ch-1)*45
    vals=[f'CH{ch} / J{ch+1}',f'R1{ch}1 + R1{ch}2',f'U{ch+2}',f'R1{ch}3 + R1{ch}4',f'C1{ch}1',f'C1{ch}2',f'{18-2*ch} / {17-2*ch}']
    for (x,_),s in zip(headers,vals):d.text(x,y,s,22)
    u=f'U{ch+2}';c=f'C1{ch}2'
    same((u,5),(c,1),('U2',5));same((u,2),(c,2),('U2',2))
d.panel(40,1265,2315,510,'3  RLD feedback and J8 bias output')
d.text(75,1415,'U1 pin 63',23,bold=True);d.text(75,1450,'RLDOUT',21,GREEN)
d.wire([(230,1410),(780,1410)],GREEN);d.dot(340,1410,GREEN)
d.resistor(780,1410,'R22',170,GREEN);d.wire([(950,1410),(1350,1410)],GREEN);d.dot(1110,1410,GREEN)
d.resistor(1350,1410,'R23',170,GREEN);d.wire([(1520,1410),(2020,1410)],GREEN)
d.text(2050,1417,'J8 pin 1 → bias electrode',22,bold=True)
d.text(2050,1460,'J8 pin 2: NC',21,MUTED)
d.wire([(340,1410),(340,1530),(425,1530)],GREEN);d.resistor(425,1530,'R21',170,GREEN)
d.wire([(595,1530),(700,1530),(700,1650),(795,1650)],GREEN)
d.wire([(340,1530),(340,1630),(440,1630)],GREEN);d.dot(340,1530,GREEN)
# Horizontal capacitor for the parallel RLD branch.
d.wire([(440,1630),(495,1630)],GREEN);d.wire([(495,1614),(495,1646)],GREEN)
d.wire([(511,1614),(511,1646)],GREEN);d.wire([(511,1630),(700,1630)],GREEN);d.dot(700,1630,GREEN)
d.text(500,1685,'C23  1.5 nF',21,anchor='middle');d.text(820,1657,'U1 pin 61 RLDINV',22,bold=True)
d.box(1050,1500,390,170,'#e8f4ee','#71a288');d.wire([(1110,1410),(1110,1500)],GREEN)
d.text(1075,1540,'U9 · TPD4E001',25,bold=True);d.text(1075,1577,'pin 1: RLD_CLAMP tap',21)
d.text(1075,1613,'pin 5 → AVDD; pin 2 → GND',20);d.text(1075,1648,'pins 3, 4, 6: NC',20)
d.text(1530,1565,'C24 100 nF: AVDD → capacitor → GND',22)
d.text(1530,1610,'R21 and C23 both bridge pins 63 and 61.',22,GREEN)
d.text(1530,1660,'RLD starts disabled; this drawing shows its wiring.',20,MUTED)
same(('U1',63),('R21',1),('C23',1),('R22',1),('TP6',1));same(('U1',61),('R21',2),('C23',2))
same(('R22',2),('R23',1),('U9',1));same(('R23',2),('J8',1));same(('U9',5),('C24',1),('U2',5));same(('U9',2),('C24',2),('U2',2))
d.text(65,1825,'Test points: TP1 AVDD · TP2 VSYS · TP3 VREFP · TP4 VCAP1 · TP5 DRDY_N · TP6 RLDOUT · TP7 3V3_D · TP8 GND',21,MUTED)
d.footer('No galvanic isolation is fitted: do not connect electrodes to a person while USB or other externally grounded equipment is attached.')
d.save('03_protection_and_bias')

report={'source':'Fresh KiCad XML export from CapFix schematic','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'provider':'Locally drawn SVG from schematic; Fal unavailable in this session','passed':True,
        'connection_groups_checked':len(checks),'checks':checks,
        'note':'Electrical connectivity picture; pin locations rearranged for readability. Not a physical package pinout or PCB layout.'}
(ROOT/'diagram_connection_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f'Created three SVG wiring pictures; checked {len(checks)} connection groups against the freshly exported netlist.')
