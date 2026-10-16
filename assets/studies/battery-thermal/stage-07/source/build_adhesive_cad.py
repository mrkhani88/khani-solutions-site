"""Create native/neutral CAD for each adhesive thickness; FreeCAD open-source CAD required."""
from pathlib import Path
import json,sys,os,itertools
sys.path.extend([os.environ.get('FREECAD_LIB','/Applications/FreeCAD.app/Contents/Resources/lib'),'/usr/lib/freecad/lib'])
import FreeCAD as F,Part
R=Path(__file__).resolve().parents[1];cases=json.loads((R/'source/sweep.json').read_text())['cases'];proof={}
def face(shape,z):return next(f for f in shape.Faces if abs(f.CenterOfMass.z-z)<1e-7 and abs(f.normalAt(0,0).z)>.99)
for case,c in cases.items():
    d=F.openDocument(str(R/'cad/Battery_Product_R5_large.FCStd'));d.Label='Stage 07 | '+c['label'];x,y,xx,yy=c['footprint_mm'];area=(xx-x)*(yy-y)
    ta=c['adhesive_thickness_mm'];bottom=7-ta-.1
    d.RFPad.Shape=Part.makeBox(16,5,bottom-4.8,F.Vector(47,54,4.8));d.RFPad.Label='RF pad | '+format(bottom-4.8,'.3f')+' mm installed'
    if hasattr(d.RFPad,'installed_thickness_mm'):d.RFPad.installed_thickness_mm=bottom-4.8
    for name,z,t in [('GraphiteSpreader',bottom,.1),('SpreaderAdhesive',7-ta,ta)]:
        o=d.getObject(name);o.Shape=Part.makeBox(xx-x,yy-y,t,F.Vector(x,y,z));o.Label=name+' | '+str(xx-x)+' x '+str(yy-y)+' x '+str(t)+' mm'
        if hasattr(o,'thickness_mm'):o.thickness_mm=t
    sh=d.getObject('Stage05Assumptions');sh.Label='Stage 07 adhesive assumptions';sh.set('A3','Graphite footprint: '+str(c['footprint_mm'])+' mm; thickness .10 mm');sh.set('A4','Adhesive: '+str(ta)+' mm, k=.2 W/mK, finite capacity');sh.set('A5','Adhesive '+str(ta)+' mm; pad '+str(bottom-4.8)+' mm; exterior unchanged');sh.set('A6','Fixed50x70mm graphite; kxy800/kz5, adhesivek.2; no experimental validation.');d.getObject('Stage04Assumptions').Label='Historical Stage04 assumptions (pad superseded)';d.getObject('Stage04Assumptions').set('A4','Original pad2.2mm; current fitted pad '+str(bottom-4.8)+' mm');d.recompute()
    objs=[o for o in d.Objects if hasattr(o,'ReviewColor')];overlaps=[]
    for a,b in itertools.combinations(objs,2):
        if a.Shape.BoundBox.intersect(b.Shape.BoundBox):
            v=a.Shape.common(b.Shape).Volume
            if v>1e-5:overlaps.append([a.Name,b.Name,v])
    assert not overlaps,overlaps
    contacts={'pad_to_graphite_mm2':face(d.RFPad.Shape,bottom).common(face(d.GraphiteSpreader.Shape,bottom)).Area,'graphite_to_adhesive_mm2':face(d.GraphiteSpreader.Shape,7-ta).common(face(d.SpreaderAdhesive.Shape,7-ta)).Area,'adhesive_to_cover_mm2':face(d.SpreaderAdhesive.Shape,7).common(face(d.BackGlass.Shape,7)).Area}
    assert abs(contacts['pad_to_graphite_mm2']-80)<1e-6 and abs(contacts['graphite_to_adhesive_mm2']-area)<1e-6 and abs(contacts['adhesive_to_cover_mm2']-area)<1e-6
    native=R/'cad'/('Battery_Product_R6_'+case+'.FCStd');step=R/'cad'/('Battery_Product_R6_'+case+'.step');d.saveAs(str(native));Part.export(objs,str(step));neutral=Part.Shape();neutral.read(str(step));assert len(neutral.Solids)==67;assert abs(neutral.Volume-sum(o.Shape.Volume for o in objs))/neutral.Volume<1e-7
    mesh=[]
    for o in objs:
        assert o.Shape.isValid() and len(o.Shape.Solids)==1
        v,t=o.Shape.tessellate(.16);mesh.append({'id':o.Name,'label':o.Label,'group':o.ReviewGroup,'color':json.loads(o.ReviewColor),'visible':o.DefaultVisible,'vertices':[[q.x,q.y,q.z] for q in v],'triangles':t})
    (R/'results'/(case+'_assembly_mesh.json')).write_text(json.dumps(mesh,separators=(',',':')))
    proof[case]={'valid_solids':67,'overlaps':overlaps,'step_solids':67,'step_volume_matches':True,'contacts_mm2':contacts,'pad_thickness_mm':bottom-4.8,'graphite_z_mm':[bottom,7-ta],'adhesive_z_mm':[7-ta,7],'outer_enclosure_unchanged':True};F.closeDocument(d.Name)
(R/'evidence/geometry_verification.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof,indent=2))
