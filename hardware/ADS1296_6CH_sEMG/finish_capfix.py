"""Incremental local routing corrections. See final DRC and distance audit."""
import route_local as r
import pcbnew as p
import sys,json

def remove_ids(ids):
    for t in list(r.b.GetTracks()):
        if t.m_Uuid.AsString() in ids:r.held.append(t);r.b.Remove(t)
    r.idx=r.obstacles()

try:
    if sys.argv[1]=='reference':
        # Replace the old transverse ground branch with individual local returns
        # so VREFP can reach a nearby via directly behind the reference pins.
        remove_ids({'89794483-1485-4887-865f-3cb32ef7a066','ea55a37f-1392-49f7-bbc7-106b688f89aa'})
        exists=any(isinstance(t,p.PCB_VIA) and t.GetNetname()=='VREFP' and r.xy(t.GetPosition())==(71.75,71.4) for t in r.b.GetTracks())
        v=(71.75,71.4) if exists else r.fanout(('U1','24'),[(71.75,71.4)])
        if not exists:r.connect(v,r.xy(r.ps['C14','1'].GetPosition()),'VREFP',p.B_Cu,.15,.1)
        print('C14 reference signal via',v,flush=True)
        v=r.ground('C14');r.connect(r.xy(r.ps['U1','25'].GetPosition()),v,'GND',p.F_Cu,.15,.1)
        print('C14 dedicated ground via',v,flush=True)
    elif sys.argv[1]=='bias':
        remove_ids({'2f5d64bd-a666-4860-9b1d-cef523eab806','18cfa6c2-6f7b-4624-87a9-30b412b02bcd',
                    '195b52e1-a703-41ac-9fcd-ee5d0e7083cd','308f3254-1f5a-4f73-9c20-19f570d9de4d'})
        r.local['ground_vias'].pop('C27',None)
        for ref,pin,cp in [('C27','54','1'),('R21','61','2'),('R21','63','1')]:
            preferences={'54':[(73.35,60.2375)],'61':[(69.75,62.6)],'63':[(68.75,60.2375)]}
            v=r.fanout(('U1',pin),preferences[pin]);r.connect(v,r.xy(r.ps[ref,cp].GetPosition()),r.ps[ref,cp].GetNetname(),p.B_Cu,.15,.1)
            print(ref,pin,'via',v,flush=True)
        for num in ['1','2']:r.padconnect(('R21',num),('C23',num))
        print('C27 new local GND',r.ground('C27'),flush=True)
    elif sys.argv[1]=='grounds':
        for ref in ['C22','C10','C20','C27','C12','C7','C15']:
            if ref in r.local['ground_vias']:continue
            print('Ground',ref,r.ground(ref),flush=True)
    elif sys.argv[1]=='support':
        for first,second in [
            (('C14','1'),('C15','1')),(('C14','1'),('TP3','1')),
            (('R21','1'),('R22','1')),(('R21','1'),('TP6','1')),
            (('U1','43'),('R34','1')),(('U1','48'),('C12','1')),
            (('U1','22'),('C7','1')),(('U1','54'),('C8','1'))]:
            r.padconnect(first,second);print('Connected',first,second,flush=True)
    elif sys.argv[1]=='repair':
        # Pin62 needs a short jog around the nearby RLDINV via before its
        # AVDD via. A straight radial fanout has insufficient clearance.
        if not any(isinstance(t,p.PCB_VIA) and t.GetNetname()=='AVDD' and r.xy(t.GetPosition())==(69.15,63.25) for t in r.b.GetTracks()):
            q=(69.15,63.25);assert r.viaok(q,'AVDD')
            r.connect(r.xy(r.ps['U1','62'].GetPosition()),q,'AVDD',p.F_Cu,.15,.1);r.via(q,'AVDD');r.save()
        rows=[
            (('C12','1'),('C13','1')),(('U1','55'),('C19','1')),
            (('U1','52'),('R14','2')),(('U1','64'),('C21','1')),
            (('U1','28'),('C17','1')),(('C17','1'),('C16','1')),
            (('U1','42'),('R10','1')),(('U1','45'),('R12','1')),
            (('R34','2'),('A1','17')),
            (('U1','56'),('C9','1'))]
        for first,second in rows:
            g=r.TraceGraph(r.b,r.ps[first].GetNetname(),[a for a in r.allpads if a.GetNetname()==r.ps[first].GetNetname()])
            if g.pads_path(first,second)['found']:continue
            r.padconnect(first,second);print('Repaired',first,second,flush=True);r.save()
        for ref,pn in [('U1','20'),('U1','23'),('U1','57'),('U1','58'),('U1','62'),('C10','1'),('C27','1'),('C9','1')]:
            net=r.ps[ref,pn].GetNetname();g=r.TraceGraph(r.b,net,[a for a in r.allpads if a.GetNetname()==net]);goals=[n for vs in g.via_nodes.values() for n in vs]
            if not g.shortest(g.pad_nodes[ref,pn],goals)['found']:print('Plane connection',ref,pn,r.fanout((ref,pn)),flush=True);r.save()
    elif sys.argv[1]=='fix_labels':
        for t in r.b.GetDrawings():
            if isinstance(t,p.PCB_TEXT) and t.GetText()=='ADS1296 / TINY SOCKET / A4 CAPFIX':t.SetText('ADS1296 / A4 CAPFIX')
    elif sys.argv[1]=='cleanup':
        report=json.loads((r.BASE.parents[1]/'tmp/capfix/route_drc.json').read_text())
        ids={item['uuid'] for v in report['violations'] if v['type'] in ['track_dangling','via_dangling'] for item in v['items']}
        remove_ids(ids);print('Removed obsolete dangling routing objects:',len(ids),flush=True)
    else:raise ValueError(sys.argv[1])
finally:r.save()
