"""Add the assumed pad to a COPY of R2 CAD; original files stay unchanged.
Run with FreeCAD's Python. Set FREECAD_LIB if its modules are not already visible.
"""
from pathlib import Path
import sys,os,json
sys.path.extend([os.environ.get('FREECAD_LIB','/Applications/FreeCAD.app/Contents/Resources/lib'),'/usr/lib/freecad/lib'])
import FreeCAD as A,Part
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'source/inputs.json').read_text())['rf_pad']
doc=A.openDocument(str(ROOT/'cad/Battery_Product_R2.FCStd'))
doc.Label='Stage 04 RF board thermal pad | independent assumed assembly'
g=doc.addObject('App::DocumentObjectGroup','RFPadStudy');g.Label='08 RF board to enclosure thermal pad'
pad=doc.addObject('Part::Feature','RFPad');pad.Label='PAD01 | RF PCB to back cover, 16 x 5 x 2.2 mm'
x0,y0,x1,y1=P['footprint_global_mm'];z=P['bottom_z_mm'];thickness=P['installed_thickness_mm']
pad.Shape=Part.makeBox(x1-x0,y1-y0,thickness,A.Vector(x0,y0,z));g.addObject(pad)
for k,value in [('MaterialCandidate','Assumed thermal gap pad, k=3 W/mK; not a commercial product'),('Evidence',P['basis']),('ReviewColor',json.dumps([.25,.72,.70])),('ReviewGroup','RFPadStudy')]:
    pad.addProperty('App::PropertyString',k,'Study');setattr(pad,k,value)
pad.addProperty('App::PropertyBool','DefaultVisible','Study');pad.DefaultVisible=True
pad.addProperty('App::PropertyFloat','IllustrativePowerW','Study');pad.IllustrativePowerW=0
for key,value in [('Conductivity_W_mK',P['k_W_mK']),('Density_kg_m3',P['rho_kg_m3']),('SpecificHeat_J_kgK',P['cp_J_kgK']),('ContactResistanceEach_m2K_W',P['contact_resistance_each_m2K_W'])]:
    pad.addProperty('App::PropertyFloat',key,'ThermalAssumptions');setattr(pad,key,value)
sheet=doc.addObject('Spreadsheet::Sheet','Stage04Assumptions');sheet.Label='Stage 04 applied heat and pad assumptions'
for cell,value in {'A1':'INDEPENDENT ASSUMED TEACHING STUDY','A2':'Same combined sources before/after: cell 2 W + electronics 1.75 W','A3':'Older CAD package powers are illustrative; active source is inputs.json','A4':'Pad: 16 x 5 x 2.2 mm installed; k=3; rho=2200; cp=1000','A5':'Each interface resistance: 0.0002 m2 K/W; not calibrated','A6':'No compression mechanics or experimentally validated product prediction'}.items():sheet.set(cell,value)
sheet.setColumnWidth('A',680);doc.recompute()
objects=[o for o in doc.Objects if hasattr(o,'ReviewColor')]
overlaps=[]
for o in objects:
    assert o.Shape.isValid() and len(o.Shape.Solids)==1
    if o!=pad and o.Shape.BoundBox.intersect(pad.Shape.BoundBox):
        vol=o.Shape.common(pad.Shape).Volume
        if vol>1e-5:overlaps.append({'component':o.Name,'pad_overlap_mm3':vol})
assert not overlaps,overlaps
assert abs(pad.Shape.Volume-176)<1e-8
doc.saveAs(str(ROOT/'cad/Battery_Product_R3_RFPad.FCStd'))
Part.export(objects,str(ROOT/'cad/Battery_Product_R3_RFPad.step'))
Part.export([pad],str(ROOT/'cad/RF_Thermal_Pad.step'))
neutral=Part.Shape();neutral.read(str(ROOT/'cad/Battery_Product_R3_RFPad.step'))
assert len(neutral.Solids)==len(objects)
assert abs(neutral.Volume-sum(o.Shape.Volume for o in objects))/neutral.Volume<1e-7
mesh=[]
for o in objects:
    vertices,tris=o.Shape.tessellate(.16)
    mesh.append({'id':o.Name,'label':o.Label,'group':o.ReviewGroup,'color':json.loads(o.ReviewColor),'visible':o.DefaultVisible,'vertices':[[p.x,p.y,p.z] for p in vertices],'triangles':tris})
(ROOT/'results/assembly_mesh.json').write_text(json.dumps(mesh,separators=(',',':')))
proof={'valid_solids':len(objects),'pad_volume_mm3':pad.Shape.Volume,'pad_board_contact_area_mm2':80,'pad_cover_contact_area_mm2':80,'pad_clear_of_packages':True,'overlaps':overlaps,'step_solids':len(neutral.Solids),'step_volume_matches':True,'pad_geometry_basis':'Assumed concept; installed thickness fills existing 4.8-to-7.0 mm clearance'}
(ROOT/'evidence/geometry_verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))
