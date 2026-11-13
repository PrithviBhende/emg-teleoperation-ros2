"""Obstacle-aware local routing; all results require native KiCad DRC."""
from pathlib import Path
from collections import defaultdict
import math,heapq,json,sys
import pcbnew as p
from trace_graph import TraceGraph,xy
BASE=Path(__file__).resolve().parent;NAME='ADS1296_RevA4_TinySocket'
file=BASE/(NAME+'.kicad_pcb');b=p.LoadBoard(str(file));mm=p.FromMM
def pt(x,y):return p.VECTOR2I(mm(x),mm(y))
fs={f.GetReference():f for f in b.GetFootprints()}
ps={(f.GetReference(),a.GetNumber()):a for f in fs.values() for a in f.Pads() if a.GetNumber()}
allpads=list(ps.values());layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
local=json.loads((BASE/'local_routes.json').read_text())
held=[]
def obstacles():
    idx=defaultdict(list)
    for a in [*allpads,*b.GetTracks()]:
        bb=a.GetBoundingBox();bb.Inflate(mm(.7))
        for layer in layers:
            if not a.IsOnLayer(layer):continue
            shape=a.GetEffectiveShape(layer)
            for ix in range(math.floor(p.ToMM(bb.GetLeft())),math.ceil(p.ToMM(bb.GetRight()))+1):
                for iy in range(math.floor(p.ToMM(bb.GetTop())),math.ceil(p.ToMM(bb.GetBottom()))+1):idx[layer,ix,iy].append((a,shape))
    return idx
idx=obstacles()
def pointok(q,net,layer,radius=.226):
    x,y=q
    if not(20.8<x<119.2 and 20.8<y<99.2):return False
    if 96.6<x<109.4 and y<25.9:return False
    return all(a.GetNetname()==net or not shape.Collide(pt(x,y),mm(radius)) for a,shape in idx[layer,math.floor(x),math.floor(y)])
def lineok(a,z,net,layer,width=.15):
    n=max(1,math.ceil(math.dist(a,z)/.045))
    return all(pointok((a[0]+(z[0]-a[0])*i/n,a[1]+(z[1]-a[1])*i/n),net,layer,.151+width/2) for i in range(n+1))
def viaok(q,net):
    x,y=q
    if 96.1<x<109.9 and 25.6<y<42.9:return False
    if any(a.GetAttribute()==p.PAD_ATTRIB_SMD and a.GetEffectiveShape(a.GetParentFootprint().GetLayer()).Collide(pt(x,y),mm(.35)) for a in allpads):return False
    if any(not pointok(q,net,l,.451) for l in layers):return False
    return not any(isinstance(t,p.PCB_VIA) and math.dist(q,xy(t.GetPosition()))<.62 for t in b.GetTracks())
def track(seq,net,layer=p.F_Cu,width=.15):
    global idx
    for a,z in zip(seq,seq[1:]):
        if math.dist(a,z)<1e-6:continue
        t=p.PCB_TRACK(b);t.SetStart(pt(*a));t.SetEnd(pt(*z));t.SetNet(b.FindNet(net));t.SetLayer(layer);t.SetWidth(mm(width));t.SetLocked(True);b.Add(t)
    idx=obstacles()
def via(q,net):
    global idx
    v=p.PCB_VIA(b);v.SetPosition(pt(*q));v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));v.SetLocked(True);b.Add(v);idx=obstacles();return v
def save():
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(file),b)
    (BASE/'local_routes.json').write_text(json.dumps(local,indent=2))
def elbows(a,z):
    dx,dy=z[0]-a[0],z[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;k=min(abs(dx),abs(dy))
    return [[a,(a[0]+sx*k,a[1]+sy*k),z],[a,(z[0]-sx*k,z[1]-sy*k),z]]
def direct(a,z,net,layer,width=.15):
    for seq in elbows(a,z):
        if all(lineok(x,y,net,layer,width) for x,y in zip(seq,seq[1:])):return seq
    return None
def connect(a,z,net,layer,width=.15,step=.2):
    seq=direct(a,z,net,layer,width)
    if seq:track(seq,net,layer,width);return seq
    cache={};margin=8
    xmin,xmax=min(a[0],z[0])-margin,max(a[0],z[0])+margin;ymin,ymax=min(a[1],z[1])-margin,max(a[1],z[1])+margin
    def q(k):return k[0]*step,k[1]*step
    def valid(k):
        if k not in cache:
            x,y=q(k);cache[k]=xmin<x<xmax and ymin<y<ymax and pointok((x,y),net,layer,.151+width/2)
        return cache[k]
    def near(v):
        cx,cy=round(v[0]/step),round(v[1]/step);out=[]
        for dx in range(-3,4):
            for dy in range(-3,4):
                k=cx+dx,cy+dy
                if valid(k) and lineok(v,q(k),net,layer,width):out.append(k)
        return out
    starts=near(a);goals=set(near(z))
    if not starts or not goals:raise RuntimeError(f'{net}: no grid escape {a} -> {z} on {layer}')
    cost={k:math.dist(a,q(k)) for k in starts};prev={};queue=[(c+math.dist(q(k),z),c,k) for k,c in cost.items()];heapq.heapify(queue);end=None
    dirs=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]
    while queue:
        _,c,here=heapq.heappop(queue)
        if c>cost[here]+1e-8:continue
        if here in goals:end=here;break
        olddir=(here[0]-prev[here][0],here[1]-prev[here][1]) if here in prev else None
        for dx,dy in dirs:
            other=here[0]+dx,here[1]+dy
            if not valid(other):continue
            mid=((here[0]+other[0])*step/2,(here[1]+other[1])*step/2)
            if not pointok(mid,net,layer,.151+width/2):continue
            new=c+step*math.hypot(dx,dy)+(.035 if olddir and olddir!=(dx,dy) else 0)
            if new<cost.get(other,math.inf):cost[other]=new;prev[other]=here;heapq.heappush(queue,(new+math.dist(q(other),z),new,other))
    if end is None:raise RuntimeError(f'{net}: no path {a} -> {z} on {layer}')
    seq=[end]
    while seq[-1] in prev:seq.append(prev[seq[-1]])
    raw=[a,*[q(k) for k in reversed(seq)],z];simple=[raw[0]];i=0
    while i<len(raw)-1:
        for j in range(len(raw)-1,i,-1):
            candidate=direct(raw[i],raw[j],net,layer,width)
            if candidate:simple.extend(candidate[1:]);i=j;break
        else:raise RuntimeError('Path could not be smoothed')
    assert all(lineok(x,y,net,layer,width) for x,y in zip(simple,simple[1:])),net
    track(simple,net,layer,width);return simple
def fanout(key,preferred=None):
    a=ps[key];net=a.GetNetname();q=xy(a.GetPosition());layer=a.GetParentFootprint().GetLayer()
    options=[]
    if preferred:options+=preferred
    for r in [.95,1.2,1.45,1.7,2,2.5,3,4]:
        for deg in range(0,360,15):options.append((round(q[0]+r*math.cos(math.radians(deg)),4),round(q[1]+r*math.sin(math.radians(deg)),4)))
    for v in options:
        if viaok(v,net) and lineok(q,v,net,layer):track([q,v],net,layer);via(v,net);return v
    raise RuntimeError('No via fanout '+str(key))
def padconnect(k1,k2,width=.15):
    a,z=ps[k1],ps[k2];assert a.GetNetname()==z.GetNetname()
    net=a.GetNetname();aa,zz=xy(a.GetPosition()),xy(z.GetPosition())
    # Reuse already-routed copper and repair its smallest remaining gap.
    g=TraceGraph(b,net,[a for a in allpads if a.GetNetname()==net])
    def component(nodes):
        seen=set(nodes);todo=list(nodes)
        while todo:
            for edge in g.edges.get(todo.pop(),[]):
                node=edge[0]
                if node not in seen:seen.add(node);todo.append(node)
        return seen
    left,right=component(g.pad_nodes[k1]),component(g.pad_nodes[k2])
    if left & right:return []
    candidates=sorted((math.dist(x[:2],y[:2]),x,y) for x in left for y in right if x[2]==y[2] and x[2] in [p.F_Cu,p.B_Cu,p.In2_Cu])
    for distance,x,y in candidates[:12]:
        if distance>8:break
        try:return connect(x[:2],y[:2],net,x[2],width,.1)
        except RuntimeError:continue
    al,zl=a.GetParentFootprint().GetLayer(),z.GetParentFootprint().GetLayer()
    if al==zl:
        try:return connect(aa,zz,net,al,width)
        except RuntimeError:pass
    oldleft=[n[:2] for n in left if n[2]==p.B_Cu]
    oldright=[n[:2] for n in right if n[2]==p.B_Cu]
    av=min(oldleft,key=lambda q:math.dist(q,zz)) if oldleft else (fanout(k1) if a.GetAttribute()==p.PAD_ATTRIB_SMD and al!=p.B_Cu else aa)
    zv=min(oldright,key=lambda q:math.dist(q,av)) if oldright else (fanout(k2) if z.GetAttribute()==p.PAD_ATTRIB_SMD and zl!=p.B_Cu else zz)
    return connect(av,zv,net,p.B_Cu,width)
def ground(ref):
    q=fanout((ref,'2'));local['ground_vias'][ref]=list(q);return q

if __name__=='__main__':
    mode=sys.argv[1]
    try:
        if mode=='critical':
            # Signal pins first, then independent ground returns.
            for ref,pin in [('C10','59'),('C20','26'),('C22','48')]:
                a,z=ps['U1',pin],ps[ref,'1'];connect(xy(a.GetPosition()),xy(z.GetPosition()),a.GetNetname(),p.F_Cu,.15,.1);print('Direct top:',ref,flush=True)
            for ref,pin in [('C14','24'),('C27','54'),('R21','61')]:
                cp='2' if ref=='R21' else '1';v=fanout(('U1',pin));connect(v,xy(ps[ref,cp].GetPosition()),ps[ref,cp].GetNetname(),p.B_Cu,.15,.1);print('Local underside:',ref,flush=True)
            v=fanout(('U1','63'));connect(v,xy(ps['R21','1'].GetPosition()),'RLDOUT',p.B_Cu,.15,.1)
            for num in ['1','2']:padconnect(('R21',num),('C23',num))
            for ref in ['C22','C10','C14','C20','C27','C12','C7','C15']:ground(ref);print('Local ground:',ref,flush=True)
            # A dedicated reference-return connection to VREFN pin25.
            v=fanout(('U1','25'));connect(v,xy(ps['C14','2'].GetPosition()),'GND',p.B_Cu,.15,.1)
        elif mode=='connect':
            k1=tuple(sys.argv[2].split('.'));k2=tuple(sys.argv[3].split('.'));padconnect(k1,k2)
        elif mode=='ground':
            for ref in sys.argv[2:]:ground(ref)
        elif mode=='fill':pass
        else:raise ValueError(mode)
    finally:save()
