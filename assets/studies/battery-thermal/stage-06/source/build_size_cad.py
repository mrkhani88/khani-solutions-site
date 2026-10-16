"""Create native/neutral CAD for each sheet size; FreeCAD open-source CAD required."""
from pathlib import Path
import json,sys,os,itertools
sys.path.extend([os.environ.get('FREECAD_LIB','/Applications/FreeCAD.app/Contents/Resources/lib'),'/usr/lib/freecad/lib'])
import FreeCAD as F,Part
R=Path(__file__).resolve().parents[1];cases=json.loads((R/'source/sweep.json').read_text())['cases'];proof={}
def face(shape,z):return next(f for f in shape.Faces if abs(f.CenterOfMass.z-z)<1e-7 and abs(f.normalAt(0,0).z)>.99)
for case,c in cases.items():
    d=F.openDocument(str(R/'cad/Battery_Product_R4_Graphite.FCStd'));d.Label='Stage 06 | '+c['label'];x,y,xx,yy=c['footprint_mm'];area=(xx-x)*(yy-y)
    for name,z,t in [('GraphiteSpreader',6.875,.1),('SpreaderAdhesive',6.975,.025)]:
        o=d.getObject(name);o.Shape=Part.makeBox(xx-x,yy-y,t,F.Vector(x,y,z));o.Label=name+' | '+str(xx-x)+' x '+str(yy-y)+' x '+str(t)+' mm'
    sh=d.getObject('Stage05Assumptions');sh.Label='Stage 06 footprint assumptions';sh.set('A3','Graphite footprint: '+str(c['footprint_mm'])+' mm; thickness .10 mm');sh.set('A5','Every size: pad 2.075 mm; enclosure unchanged');sh.set('A6','Fixed lower-right corner (68,30); grow left/up toward battery. No experimental validation.');d.recompute()
    objs=[o for o in d.Objects if hasattr(o,'ReviewColor')];overlaps=[]
    for a,b in itertools.combinations(objs,2):
        if a.Shape.BoundBox.intersect(b.Shape.BoundBox):
            v=a.Shape.common(b.Shape).Volume
            if v>1e-5:overlaps.append([a.Name,b.Name,v])
    assert not overlaps,overlaps
    contacts={'pad_to_graphite_mm2':face(d.RFPad.Shape,6.875).common(face(d.GraphiteSpreader.Shape,6.875)).Area,'graphite_to_adhesive_mm2':face(d.GraphiteSpreader.Shape,6.975).common(face(d.SpreaderAdhesive.Shape,6.975)).Area,'adhesive_to_cover_mm2':face(d.SpreaderAdhesive.Shape,7).common(face(d.BackGlass.Shape,7)).Area}
    assert abs(contacts['pad_to_graphite_mm2']-80)<1e-6 and abs(contacts['graphite_to_adhesive_mm2']-area)<1e-6 and abs(contacts['adhesive_to_cover_mm2']-area)<1e-6
    native=R/'cad'/('Battery_Product_R5_'+case+'.FCStd');step=R/'cad'/('Battery_Product_R5_'+case+'.step');d.saveAs(str(native));Part.export(objs,str(step));neutral=Part.Shape();neutral.read(str(step));assert len(neutral.Solids)==67;assert abs(neutral.Volume-sum(o.Shape.Volume for o in objs))/neutral.Volume<1e-7
    mesh=[]
    for o in objs:
        assert o.Shape.isValid() and len(o.Shape.Solids)==1
        v,t=o.Shape.tessellate(.16);mesh.append({'id':o.Name,'label':o.Label,'group':o.ReviewGroup,'color':json.loads(o.ReviewColor),'visible':o.DefaultVisible,'vertices':[[q.x,q.y,q.z] for q in v],'triangles':t})
    (R/'results'/(case+'_assembly_mesh.json')).write_text(json.dumps(mesh,separators=(',',':')))
    proof[case]={'valid_solids':67,'overlaps':overlaps,'step_solids':67,'step_volume_matches':True,'contacts_mm2':contacts,'pad_thickness_mm':2.075,'graphite_z_mm':[6.875,6.975],'adhesive_z_mm':[6.975,7],'outer_enclosure_unchanged':True};F.closeDocument(d.Name)
(R/'evidence/geometry_verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))
