"""Build a non-overlapping bonded graphite stack inside the unchanged enclosure.
Run with FreeCAD Python; FREECAD_LIB can locate the optional CAD modules.
"""
from pathlib import Path
import os,sys,json,itertools
sys.path.extend([os.environ.get('FREECAD_LIB','/Applications/FreeCAD.app/Contents/Resources/lib'),'/usr/lib/freecad/lib'])
import FreeCAD as F,Part
ROOT=Path(__file__).resolve().parents[1];P=json.loads((ROOT/'source/inputs.json').read_text());G=P['graphite'];A=P['spreader_adhesive']
top=7-A['thickness_mm'];bottom=top-G['thickness_mm'];pad_t=bottom-4.8
doc=F.openDocument(str(ROOT/'cad/Battery_Product_R3_RFPad.FCStd'));doc.Label='Stage 05 bonded graphite spreader | independent assumed assembly'
pad=doc.getObject('RFPad');x,y,xx,yy=P['rf_pad']['footprint_global_mm'];pad.Shape=Part.makeBox(xx-x,yy-y,pad_t,F.Vector(x,y,4.8));pad.Label='PAD01 | RF pad, 16 x 5 x 2.075 mm installed'
group=doc.addObject('App::DocumentObjectGroup','SpreaderStudy');group.Label='09 Graphite spreader and adhesive bondline'
def add(name,label,z,t,props,color):
    x,y,xx,yy=G['footprint_global_mm'];o=doc.addObject('Part::Feature',name);o.Shape=Part.makeBox(xx-x,yy-y,t,F.Vector(x,y,z));o.Label=label;group.addObject(o)
    for key,value in [('ReviewColor',json.dumps(color)),('ReviewGroup','SpreaderStudy'),('MaterialCandidate',props['basis']),('Evidence','Independent assumed concept. Thermal properties are not vendor measurements.')]:o.addProperty('App::PropertyString',key,'Study');setattr(o,key,value)
    o.addProperty('App::PropertyBool','DefaultVisible','Study');o.DefaultVisible=True;o.addProperty('App::PropertyFloat','IllustrativePowerW','Study');o.IllustrativePowerW=0
    for key,value in props.items():
        if isinstance(value,(int,float)):o.addProperty('App::PropertyFloat',key,'ThermalAssumptions');setattr(o,key,value)
    return o
graphite=add('GraphiteSpreader','GS01 | Graphite spreader, 30 x 50 x 0.10 mm',bottom,G['thickness_mm'],G,[.19,.23,.27])
adhesive=add('SpreaderAdhesive','GS02 | Bond adhesive, 30 x 50 x 0.025 mm',top,A['thickness_mm'],A,[.45,.66,.76])
sheet=doc.addObject('Spreadsheet::Sheet','Stage05Assumptions');sheet.Label='Stage 05 fixed envelope / assumed bonded spreader'
notes=['INDEPENDENT ASSUMED THERMAL CONCEPT','Same 3.75 W source and exterior ambient conditions as Stage 04','Graphite: 30 x 50 x .10 mm, kxy=800, kz=5 W/mK','Adhesive: .025 mm, k=.2 W/mK, finite heat capacity','Pad shortened 2.2 -> 2.075 mm; enclosure stays unchanged','Control: identical stack and mass, only graphite kxy=5 W/mK','No experimental validation, compression mechanics or safety qualification']
for i,n in enumerate(notes,1):sheet.set('A'+str(i),n)
sheet.setColumnWidth('A',690);doc.recompute();objects=[o for o in doc.Objects if hasattr(o,'ReviewColor')]
overlaps=[]
for a,b in itertools.combinations(objects,2):
    if a.Shape.BoundBox.intersect(b.Shape.BoundBox):
        volume=a.Shape.common(b.Shape).Volume
        if volume>1e-5:overlaps.append({'a':a.Name,'b':b.Name,'overlap_mm3':volume})
assert not overlaps,overlaps
def face(shape,z):return next(f for f in shape.Faces if abs(f.CenterOfMass.z-z)<1e-7 and abs(f.normalAt(0,0).z)>.99)
contacts={'pad_to_graphite_mm2':face(pad.Shape,bottom).common(face(graphite.Shape,bottom)).Area,'graphite_to_adhesive_mm2':face(graphite.Shape,top).common(face(adhesive.Shape,top)).Area,'adhesive_to_cover_mm2':face(adhesive.Shape,7).common(face(doc.BackGlass.Shape,7)).Area}
assert abs(contacts['pad_to_graphite_mm2']-80)<1e-6 and abs(contacts['graphite_to_adhesive_mm2']-1500)<1e-6 and abs(contacts['adhesive_to_cover_mm2']-1500)<1e-6
doc.saveAs(str(ROOT/'cad/Battery_Product_R4_Graphite.FCStd'));Part.export(objects,str(ROOT/'cad/Battery_Product_R4_Graphite.step'));Part.export([graphite,adhesive],str(ROOT/'cad/Graphite_Adhesive_Stack.step'))
neutral=Part.Shape();neutral.read(str(ROOT/'cad/Battery_Product_R4_Graphite.step'));assert len(neutral.Solids)==len(objects)
assert abs(neutral.Volume-sum(o.Shape.Volume for o in objects))/neutral.Volume<1e-7
mesh=[]
for o in objects:
    assert o.Shape.isValid() and len(o.Shape.Solids)==1
    v,t=o.Shape.tessellate(.16);mesh.append({'id':o.Name,'label':o.Label,'group':o.ReviewGroup,'color':json.loads(o.ReviewColor),'visible':o.DefaultVisible,'vertices':[[q.x,q.y,q.z] for q in v],'triangles':t})
(ROOT/'results/assembly_mesh.json').write_text(json.dumps(mesh,separators=(',',':')))
proof={'valid_solids':len(objects),'overlaps':overlaps,'step_solids':len(neutral.Solids),'step_volume_matches':True,'contacts_measured_from_native_faces':contacts,'installed_pad_thickness_mm':pad_t,'graphite_z_mm':[bottom,top],'adhesive_z_mm':[top,7],'outer_enclosure_unchanged':True}
(ROOT/'evidence/geometry_verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2));F.closeDocument(doc.Name)
