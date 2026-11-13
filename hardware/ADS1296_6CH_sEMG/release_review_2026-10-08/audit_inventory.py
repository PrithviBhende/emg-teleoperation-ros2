"""Read-only native PCB/BOM audit; creates only this directory's JSON report."""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone
import hashlib, json, math, re
import pcbnew as p

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
NAME = 'ADS1296_RevA4_TinySocket'
pcb = BASE / (NAME + '.kicad_pcb')
board = p.LoadBoard(str(pcb))
manifest = json.loads((BASE / 'design_manifest.json').read_text())
footprints = {f.GetReference(): f for f in board.GetFootprints()}
issues, groups = [], defaultdict(list)
physical = {r: d for r, d in manifest.items() if not r.startswith('#')}
if set(physical) != set(footprints):
    issues.append('Manifest reference inventory differs from saved PCB.')
for ref, d in physical.items():
    f = footprints.get(ref)
    if f is None:
        continue
    if f.GetFPIDAsString() != d['footprint']:
        issues.append(f'{ref}: footprint differs from manifest')
    pads = {a.GetNumber(): a for a in f.Pads() if a.GetNumber()}
    for n, net in d['nets'].items():
        pad = pads.get(n)
        if pad is None or not (pad.GetNetname() == net if net else pad.GetNetname().startswith('unconnected-')):
            issues.append(f'{ref}.{n}: net mismatch')
    if not ref.startswith(('TP', 'H')):
        groups[d['mpn']].append(ref)
bom_refs = {line.split('|')[1] for line in (BASE / 'BOM.md').read_text().splitlines()
            if re.match(r'^\|(?:[A-Z]+\d+)\|', line)}
if bom_refs != set(physical):
    issues.append('BOM.md reference list differs from native footprint list')
missing_local_libraries = []
for f in footprints.values():
    lib, fp = f.GetFPIDAsString().split(':', 1)
    path = BASE / 'footprints' / (lib + '.pretty') / (fp + '.kicad_mod')
    if not path.exists():
        missing_local_libraries.append(str(path))
root_text = (BASE / (NAME + '.kicad_sch')).read_text()
child_sheets = re.findall(r'\(property "Sheetfile" "([^"\n]+)"', root_text, re.IGNORECASE)
missing_child_sheets = [s for s in child_sheets if not (BASE / s).exists()]
drc = json.loads((OUT / 'drc_refilled_fresh.json').read_text())
erc = json.loads((OUT / 'erc_fresh.json').read_text())
six = json.loads((OUT / 'six_targets_fresh.json').read_text())
counts = {'drc': len(drc['violations']), 'unconnected': len(drc['unconnected_items']),
          'schematic_parity': len(drc['schematic_parity']),
          'erc': sum(len(s['violations']) for s in erc['sheets'])}
if any(counts.values()):
    issues.append('Fresh native checks report violations')
if not six['passed'] or six['board_sha256'] != hashlib.sha256(pcb.read_bytes()).hexdigest():
    issues.append('Six-target measurement did not pass on this exact board')
if missing_child_sheets or missing_local_libraries:
    issues.append('Missing native local dependency')
tracks = [t for t in board.GetTracks() if not isinstance(t, p.PCB_VIA)]
vias = [t for t in board.GetTracks() if isinstance(t, p.PCB_VIA)]
grouped = []
for mpn, refs in groups.items():
    d = physical[refs[0]]
    grouped.append({'mpn': mpn, 'refs': refs, 'quantity_per_board': len(refs),
                    'value': d['value'], 'footprint': d['footprint'],
                    'description': d['description'], 'datasheet': d['datasheet']})
outline_points = [(p.ToMM(v.x), p.ToMM(v.y)) for e in board.GetDrawings()
                  if e.GetLayer() == p.Edge_Cuts for v in (e.GetStart(), e.GetEnd())]
dimensions = [round(max(v[i] for v in outline_points) - min(v[i] for v in outline_points), 3)
              for i in range(2)]
result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
          'board_sha256': hashlib.sha256(pcb.read_bytes()).hexdigest(),
          'native_connectivity_and_inventory_passed': not issues,
          'issues': issues, 'fresh_checks': counts, 'dimensions_mm': dimensions,
          'copper_layers': board.GetCopperLayerCount(),
          'board_thickness_mm': p.ToMM(board.GetDesignSettings().GetBoardThickness()),
          'footprints': len(footprints), 'bom_component_positions': sum(len(r) for r in groups.values()),
          'backside': sorted(f.GetReference() for f in footprints.values() if f.GetLayer() == p.B_Cu),
          'tracks': len(tracks), 'vias': len(vias),
          'track_layers': dict(Counter(board.GetLayerName(t.GetLayer()) for t in tracks)),
          'smallest_track_width_mm': min(p.ToMM(t.GetWidth()) for t in tracks),
          'local_footprint_types': len({f.GetFPIDAsString() for f in footprints.values()}),
          'missing_local_footprints': missing_local_libraries, 'child_schematics': child_sheets,
          'missing_child_schematics': missing_child_sheets, 'grouped_bom': grouped,
          'scope': 'Read-only geometric, inventory and connectivity checks; not electrical simulation, measured noise, safety certification, socket-fit or ML validation.'}
(OUT / 'inventory_and_checks.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'grouped_bom'}, indent=2))
print('GROUPED BOM')
for g in grouped:
    print(f"{g['quantity_per_board']:2d} {g['mpn']}")
raise SystemExit(0 if not issues else 1)
