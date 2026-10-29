from pathlib import Path
import hashlib,json
B=Path(__file__).resolve().parents[1]
paths=[p for d in ['cad','renders'] for p in (B/d).iterdir() if p.is_file() and p.suffix.lower() in ['.fcstd','.step','.stl','.blend','.glb','.png']]+[B/'review/mesh.json']
print(json.dumps({str(p.relative_to(B)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
