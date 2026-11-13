"""Local capacitor correction, based on the user's saved A4 PCB.
Generated board is a separate copy. Native DRC and independent metrics required.
"""
from pathlib import Path
import pcbnew as p
import json, math, sys
from trace_graph import TraceGraph, xy
BASE=Path(__file__).resolve().parent
NAME='ADS1296_RevA4_TinySocket'
SOURCE=BASE.parents[1]/'tmp/capfix/user_before.kicad_pcb'
b=p.LoadBoard(str(SOURCE));mm=p.FromMM
def pt(x,y):return p.VECTOR2I(mm(x),mm(y))
def fps():return {f.GetReference():f for f in b.GetFootprints()}
def pads():return {(f.GetReference(),a.GetNumber()):a for f in b.GetFootprints() for a in f.Pads() if a.GetNumber()}
fs=fps();ps=pads();local=json.loads((BASE/'local_routes.json').read_text())
held=[]
def remove(t):held.append(t);b.Remove(t)
def dropids(ids):
    for t in list(b.GetTracks()):
        if t.m_Uuid.AsString() in ids:remove(t)
def graph(net):return TraceGraph(b,net,[a for a in ps.values() if a.GetNetname()==net])

# Restore the missing footprint from the previously delivered board, preserving
# its A4 schematic identity and both original connections.
if 'C152' not in fs:
    original=p.LoadBoard(str(BASE.parent/'ADS1296_RevA3_Tiny'/ 'ADS1296_RevA3_Tiny.kicad_pcb'))
    f=p.Cast_to_FOOTPRINT(next(f for f in original.GetFootprints() if f.GetReference()=='C152').Duplicate(False))
    b.Add(f)
    import xml.etree.ElementTree as ET
    c=next(c for c in ET.parse(BASE/(NAME+'.net.xml')).getroot().findall('components/comp') if c.attrib['ref']=='C152')
    f.SetPath(p.KIID_PATH(c.find('sheetpath').attrib['tstamps']+c.findtext('tstamps')))
    for a in f.Pads():a.SetNet(b.FindNet('AVDD' if a.GetNumber()=='1' else 'GND'))
fs=fps();ps=pads()
targets={'C22':48,'C10':59,'C14':24,'C20':26,'C27':54,'R21':61}
before={r:math.dist(xy(fs[r].GetPosition()),xy(ps['U1',str(n)].GetPosition())) for r,n in targets.items()}

# Remove the old explicit target branches and local returns, keeping unrelated
# electrode and manually straightened digital routes.
move={'C22':(79.65,63.25,90),'C10':(70.75,59.35,0),'C14':(71.75,72.3,0),
      'C20':(72.75,74.65,180),'C27':(73.25,61.3375,0),'R21':(68.9,61.3375,0),
      'C12':(84,61,0),'C23':(68.9,59.25,0),'C7':(71.6,78.2,270),
      'C15':(75.6,78.2,270),'R34':(82.5,66,0)}
backside={'C14','C27','R21','C23'}
ids=set()
for ref in move:
    if ref in local['ground_vias']:
        g=graph('GND');vq=local['ground_vias'][ref]
        matches=[v for v in b.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetname()=='GND' and math.dist(xy(v.GetPosition()),vq)<.002]
        for v in matches:
            row=g.shortest(g.pad_nodes[ref,'2'],g.via_nodes[v.m_Uuid.AsString()])
            ids.update(row.get('track_ids',[]));ids.add(v.m_Uuid.AsString())
        del local['ground_vias'][ref]
    if ref in targets and ref!='R21':
        row=graph(ps[ref,'1'].GetNetname()).pads_path(('U1',str(targets[ref])),(ref,'1'))
        ids.update(row.get('track_ids',[]))
    # Every track actually ending in a pad that is about to move must be redone.
    for a in fs[ref].Pads():
        for t in b.GetTracks():
            if not isinstance(t,p.PCB_VIA) and t.IsOnLayer(fs[ref].GetLayer()) and (a.HitTest(t.GetStart()) or a.HitTest(t.GetEnd())):ids.add(t.m_Uuid.AsString())
dropids(ids)
for t in list(b.GetTracks()):
    if t.GetNetname() in ['VREFP','VCAP4','RLDINV','RLDOUT']:remove(t)
for ref,(x,y,a) in move.items():
    f=fs[ref]
    if ref in backside:f.Flip(f.GetPosition(),False)
    f.SetPosition(pt(x,y));f.SetOrientationDegrees(a)
    f.Reference().SetLayer(p.B_Fab if ref in backside else p.F_Fab)
    f.Reference().SetPosition(pt(x,y-2.5));f.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))

# Copper in the target land areas must be rerouted, not left underneath new pads.
ps=pads()
for t in list(b.GetTracks()):
    for ref in move:
        for a in fs[ref].Pads():
            if t.GetNetname()==a.GetNetname() or not t.IsOnLayer(a.GetLayer()):continue
            shape=t.GetEffectiveShape(a.GetLayer())
            if shape.Collide(a.GetEffectiveShape(a.GetLayer()),mm(.151)):
                remove(t);break
        else:continue
        break

# Preserve the exact outline and module position. Identify this physical variant.
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT):
        if t.GetText()=='6 CHANNELS / 4 kSPS / TOP-SIDE ASSEMBLY':t.SetText('6 CHANNELS / 4 kSPS / CHECK BOTH SIDES')
        if t.GetText()=='ADS1296 / TINY SOCKET / A4':t.SetText('ADS1296 / TINY SOCKET / A4 CAPFIX')
b.BuildConnectivity();p.SaveBoard(str(BASE/(NAME+'.kicad_pcb')),b)
(BASE/'local_routes.json').write_text(json.dumps(local,indent=2))
(BASE/'placement_changes.json').write_text(json.dumps({'before_mm':before,'placements':move,'restored':['C152'],'source_sha256':__import__('hashlib').sha256(SOURCE.read_bytes()).hexdigest()},indent=2))
print('Saved local placements and removed',len(held),'affected copper objects.')
