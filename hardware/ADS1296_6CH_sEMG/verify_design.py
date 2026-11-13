"""CapFix inventory, pin-net, assembly and local-route measurements.
Run after native DRC/ERC. Not a circuit/noise/safety simulation.
"""
from pathlib import Path
import json, hashlib, math, re, xml.etree.ElementTree as ET
from collections import Counter
import pcbnew as p
from trace_graph import TraceGraph, xy
BASE=Path(__file__).resolve().parent
NAME='ADS1296_RevA4_TinySocket'
pcb=BASE/(NAME+'.kicad_pcb')
b=p.LoadBoard(str(pcb))
manifest=json.loads((BASE/'design_manifest.json').read_text())
local=json.loads((BASE/'local_routes.json').read_text())
fps={f.GetReference():f for f in b.GetFootprints()}
pads={(f.GetReference(),a.GetNumber()):a for f in fps.values() for a in f.Pads() if a.GetNumber()}
violations=[]
def check(ok,why):
    if not ok:violations.append(why)
check(set(fps)=={r for r in manifest if not r.startswith('#')},'Physical reference inventory mismatch')
for ref,d in manifest.items():
    if ref.startswith('#') or ref not in fps:continue
    check(fps[ref].GetFPIDAsString()==d['footprint'],f'{ref}: footprint mismatch')
    for pn,net in d['nets'].items():
        a=pads.get((ref,pn))
        check(a is not None,f'{ref}.{pn}: missing pad')
        if a is not None:
            check(a.GetNetname()==net if net else a.GetNetname().startswith('unconnected-'),f'{ref}.{pn}: expected {net}, got {a.GetNetname()}')
expected={'1':'VSYS','2':'GND','3':'3V3_D','13':'ADS_RESET_N','14':'ADS_PWDN_N','15':'ADS_START','16':'ADS_DRDY_N','17':'MCU_MISO','18':'MCU_SCLK','5':'MCU_CS','4':'MCU_MOSI'}
for pn,net in expected.items():check(pads['A1',pn].GetNetname()==net,'Tiny edge pin mismatch: '+pn)
check(len(list(fps['A1'].Pads()))==18,'Tiny socket must have 18 PTH contacts, no bottom row or underside lands')
backside={f.GetReference() for f in fps.values() if f.GetLayer()==p.B_Cu}
check(backside=={'C14','C27','R21','C23'},'Unexpected assembly-side assignment: '+str(backside))
check(all(f.GetLayer() in [p.F_Cu,p.B_Cu] for f in fps.values()),'Footprint on unexpected layer')
check(not any('0402' in f.GetFPIDAsString() or '0603' in f.GetFPIDAsString() for f in fps.values()),'Passive below 0805 detected')
check(b.GetCopperLayerCount()==4,'Wrong copper-layer count')
bb=b.GetBoardEdgesBoundingBox()
ep=[xy(v) for e in b.GetDrawings() if e.GetLayer()==p.Edge_Cuts for v in [e.GetStart(),e.GetEnd()]]
size=[round(max(a[i] for a in ep)-min(a[i] for a in ep),3) for i in range(2)]
check(all(abs(x-y)<.1 for x,y in zip(size,[100,80])),'Outline must be 100x80mm')
vias=[t for t in b.GetTracks() if isinstance(t,p.PCB_VIA)]
tracks=[t for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)]
check(not any(t.GetLayer()==p.In1_Cu for t in tracks),'Signal tracks on ground-reference layer')
uuidlist=[x.m_Uuid.AsString() for f in fps.values() for x in [f,*f.Pads(),*f.GraphicalItems(),*f.GetFields()]]
check(len(uuidlist)==len(set(uuidlist)),'Duplicate footprint/pad UUIDs')
vip=[]
for key,a in pads.items():
    if a.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
    for v in vias:
        if a.HitTest(v.GetPosition()):vip.append({'pad':'.'.join(key),'via_xy_mm':xy(v.GetPosition())})
check(not vip,'Via centres inside SMD pads: '+str(vip))
graphs={}
def graph(net):
    if net not in graphs:graphs[net]=TraceGraph(b,net,[a for a in pads.values() if a.GetNetname()==net])
    return graphs[net]
check(all(a.GetAttribute()==p.PAD_ATTRIB_PTH for a in fps['A1'].Pads()),'Socket contact not plated through-hole')
for i in range(1,19):
    a=pads['A1',str(i)]
    target=(95.38 if i<=9 else 110.62,23.59+((i-1)%9)*2.54)
    check(math.dist(xy(a.GetPosition()),target)<.001,'Socket coordinate mismatch '+str(i))
    check(abs(p.ToMM(a.GetDrillSize().x)-1)<.001,'Socket drill mismatch '+str(i))
rows=[]
targets=dict(local['cap_pins'],C14=24,C16=28,C27=54,C22=48)
for ref,pin in targets.items():
    ap=pads['U1',str(pin)];cp=pads[ref,'1']
    route=graph(ap.GetNetname()).pads_path(('U1',str(pin)),(ref,'1'))
    check(route['found'],ref+': explicit bypass route not found')
    row={'ref':ref,'pin':pin,'component_centre_to_ADC_pad_mm':round(math.dist(xy(fps[ref].GetPosition()),xy(ap.GetPosition())),3),'signal_route':route}
    if ref in local['ground_vias']:
        target=local['ground_vias'][ref]
        matched=[v for v in vias if v.GetNetname()=='GND' and math.dist(xy(v.GetPosition()),target)<.002]
        check(bool(matched),ref+': assigned local ground via missing')
        if matched:
            g=graph('GND');gv=matched[0]
            row['ground_via']=xy(gv.GetPosition())
            row['ground_route']=g.shortest(g.pad_nodes[ref,'2'],g.via_nodes[gv.m_Uuid.AsString()])
            check(row['ground_route']['found'],ref+': no explicit local ground return')
    rows.append(row)
feedback=[]
for ref in ['R21','C23']:
    for pn,ic in [('1','63'),('2','61')]:
        route=graph(pads[ref,pn].GetNetname()).pads_path(('U1',ic),(ref,pn))
        check(route['found'],'Feedback route missing '+ref+'.'+pn)
        feedback.append({'terminal':ref+'.'+pn,'ADC_pin':ic,'route':route})
d=json.loads((BASE/'routed_drc.json').read_text())
e=json.loads((BASE/'erc.json').read_text())
counts={'drc_violations':len(d['violations']),'unconnected_items':len(d['unconnected_items']),'schematic_parity':len(d['schematic_parity']),'erc_violations':sum(len(s['violations']) for s in e['sheets'])}
check(not any(counts.values()),'Native checks not clean: '+str(counts))
report={'passed':not violations,'findings':violations,'checks':counts,'board_sha256':hashlib.sha256(pcb.read_bytes()).hexdigest(),'outline_mm':size,'physical_references':len(fps),'top_side_references':len(fps)-len(backside),'back_side_references':sorted(backside),'vias_in_SMD_pads':vip,'track_count':len(tracks),'via_count':len(vias),'track_layers':dict(Counter(b.GetLayerName(t.GetLayer()) for t in tracks)),'critical_capacitors':rows,'feedback':feedback,'measurement_scope':'Explicit planar copper centreline lengths including pad travel; via depth and paths inside ground pours excluded. No physical tests.'}
(BASE/'VERIFICATION.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':report['passed'],'findings':violations,'checks':counts,'size':size,'tracks':len(tracks),'vias':len(vias)},indent=2))
raise SystemExit(0 if report['passed'] else 1)

