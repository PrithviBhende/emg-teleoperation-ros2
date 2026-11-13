"""Prepare technical drawings and an integrity-checked CapFix archive."""
from pathlib import Path
import pcbnew as p
import json,hashlib,zipfile,sys
BASE=Path(__file__).resolve().parent;NAME='ADS1296_RevA4_TinySocket'
boardfile=BASE/(NAME+'.kicad_pcb')
b=p.LoadBoard(str(boardfile));audit=json.loads((BASE/'SIX_TARGET_VERIFICATION.json').read_text())
assert audit['passed'] and audit['board_sha256']==hashlib.sha256(boardfile.read_bytes()).hexdigest()
def xy(v):return [round(p.ToMM(v.x),6),round(p.ToMM(v.y),6)]
if sys.argv[1]=='prepare':
    original=BASE.parent/'ADS1296_RevA4_TinySocket'/(NAME+'.kicad_pcb')
    source=BASE.parents[1]/'tmp/capfix/user_before.kicad_pcb'
    assert hashlib.sha256(original.read_bytes()).hexdigest()==hashlib.sha256(source.read_bytes()).hexdigest()
    old=p.LoadBoard(str(source));of={f.GetReference():f for f in old.GetFootprints()};nf={f.GetReference():f for f in b.GetFootprints()}
    changed=[]
    for ref in sorted(of):
        f,z=of[ref],nf[ref]
        assert f.GetValue()==z.GetValue() and f.GetFPIDAsString()==z.GetFPIDAsString(),ref
        if (xy(f.GetPosition()),f.GetLayer(),f.GetOrientationDegrees())!=(xy(z.GetPosition()),z.GetLayer(),z.GetOrientationDegrees()):changed.append(ref)
    def copper(board):
        return {t.m_Uuid.AsString():[t.GetNetname(),xy(t.GetStart()),xy(t.GetEnd()),board.GetLayerName(t.GetLayer()),p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())] for t in board.GetTracks()}
    oc,nc=copper(old),copper(b)
    preserved=[key for key in oc if key in nc and oc[key]==nc[key]]
    report={'source_original_unchanged':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'final_sha256':audit['board_sha256'],'changed_placements':changed,'restored_footprints':sorted(set(nf)-set(of)),'existing_values_and_packages_preserved':True,'original_copper_objects_preserved_exactly':len(preserved),'original_copper_objects':len(oc),'removed_copper_objects':len(set(oc)-set(nc)),'new_copper_objects':len(set(nc)-set(oc)),'socket_position_unchanged':xy(of['A1'].GetPosition())==xy(nf['A1'].GetPosition()),'backside_parts':sorted(f.GetReference() for f in nf.values() if f.GetLayer()==p.B_Cu)}
    (BASE/'CHANGE_AUDIT.json').write_text(json.dumps(report,indent=2))
    for f in b.GetFootprints():
        for item in f.GraphicalItems():
            if isinstance(item,p.PCB_TEXT) and item.GetLayer() in [p.F_Fab,p.B_Fab]:item.SetLayer(p.Dwgs_User)
        t=f.Reference();t.SetPosition(f.GetPosition());t.SetLayer(p.B_Fab if f.GetLayer()==p.B_Cu else p.F_Fab);t.SetVisible(True);t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));t.SetTextSize(p.VECTOR2I(p.FromMM(.65),p.FromMM(.65)));t.SetTextThickness(p.FromMM(.09))
        if f.GetReference().startswith(('J','H')):t.SetPosition(p.VECTOR2I(f.GetPosition().x,f.GetPosition().y-p.FromMM(2.8)))
        if f.GetReference()=='A1':t.SetPosition(p.VECTOR2I(p.FromMM(103),p.FromMM(34)))
        if f.GetReference() in ['A1','U1']:t.SetTextSize(p.VECTOR2I(p.FromMM(1.4),p.FromMM(1.4)))
    p.SaveBoard(str(BASE.parents[1]/'tmp/capfix/assembly_render.kicad_pcb'),b)
    print(json.dumps(report,indent=2))
elif sys.argv[1]=='package':
    for report in ['VERIFICATION.json','SIX_TARGET_VERIFICATION.json']:
        rr=json.loads((BASE/report).read_text());assert rr['passed'] and rr['board_sha256']==audit['board_sha256']
    files=[f for f in BASE.rglob('*') if f.is_file() and not any(s in f.parts for s in ['__pycache__','.history','EMG_A3.pretty']) and f.suffix not in ['.pyc','.kicad_prl','.lck'] and f.name!='PACKAGE_SHA256.json']
    hashes={f.relative_to(BASE).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    manifest=BASE/'PACKAGE_SHA256.json';manifest.write_text(json.dumps(hashes,indent=2));files.append(manifest)
    out=BASE.parent/'ADS1296_RevA4_TinySocket_CapFix_Review_Package.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in files:z.write(f,BASE.name+'/'+f.relative_to(BASE).as_posix())
    with zipfile.ZipFile(out) as z:assert z.testzip() is None
    print(str(out),len(files),'files',out.stat().st_size,'bytes; integrity OK')
else:raise ValueError('prepare|package')
