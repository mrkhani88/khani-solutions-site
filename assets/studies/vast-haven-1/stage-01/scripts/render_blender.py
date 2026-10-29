import bpy,json,math,os
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1]
data=json.loads((B/'review/mesh.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=8
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.world.color=(.32,.36,.42)
scene.view_settings.view_transform='AgX'
objects=[];mats={}
for p in data['parts']:
 coords=p['vertices'];indices=p['triangles'];m=bpy.data.meshes.new(p['id']);m.from_pydata([coords[i:i+3] for i in range(0,len(coords),3)],[],[indices[i:i+3] for i in range(0,len(indices),3)]);m.update()
 ob=bpy.data.objects.new(p['id'],m);bpy.context.collection.objects.link(ob)
 key=(tuple(p['color']),p['group'])
 if key not in mats:
  mat=bpy.data.materials.new(p['group']+'_'+str(len(mats)));mat.diffuse_color=(*p['color'],1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*p['color'],1);bs.inputs['Metallic'].default_value=.45 if p['group']=='structure' else .15;bs.inputs['Roughness'].default_value=.4 if p['group']=='structure' else .55;mats[key]=mat
 ob.data.materials.append(mats[key]);ob['group']=p['group'];ob['label']=p['label'];ob['evidence']=p['evidence'];ob['cutaway_hide']=p['cutaway_hide'];objects.append(ob)
 for poly in m.polygons:
  poly.use_smooth=p['geometry']['kind'] not in ['box'] if 'geometry' in p else False
# Text labels are editable Blender objects, separate from engineering solids.
def text(label,pos,size=.34):
 cu=bpy.data.curves.new('Label_'+label,'FONT');cu.body=label;cu.align_x='CENTER';cu.size=size;cu.extrude=.001
 ob=bpy.data.objects.new('Label_'+label,cu);bpy.context.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(math.pi/2,0,0)
 mat=bpy.data.materials.get('LabelInk')
 if not mat:mat=bpy.data.materials.new('LabelInk');mat.diffuse_color=(.06,.10,.14,1)
 ob.data.materials.append(mat);return ob
# Brand wordmark is model annotation, not a claim of affiliation.
brand=text('HAVEN-1  |  PUBLIC REFERENCE',(5.3,-2.22,.6),.24)
bpy.ops.object.camera_add(location=(-7,-13,10));camera=bpy.context.object;camera.name='Review_Camera';scene.camera=camera;camera.data.type='ORTHO'
def look(pos,target,scale):camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
for pos,power,size in [((-2,-7,12),1800,9),((10,6,9),2300,10),((12,-4,4),1200,7)]:
 bpy.ops.object.light_add(type='AREA',location=pos);li=bpy.context.object;li.data.energy=power;li.data.shape='DISK';li.data.size=size;li.rotation_euler=(Vector((5,0,0))-li.location).to_track_quat('-Z','Y').to_euler()
# Soft neutral background, no implied ground or orbital environment.
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.78,.85,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
look((-7,-14,10),(5,0,0),15.8)
bpy.ops.wm.save_as_mainfile(filepath=str(B/'cad/Haven1_Public_Reference_R1.blend'))
# Export engineering geometry only; keep cameras and label out of glTF.
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.gltf(filepath=str(B/'cad/Haven1_Public_Reference_R1.glb'),export_format='GLB',use_selection=True)
def fit_visible():
 bpy.context.view_layer.update()
 q=camera.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));pts=[ob.matrix_world@Vector(c) for ob in objects if not ob.hide_render for c in ob.bound_box]
 xs=[p.dot(right) for p in pts];ys=[p.dot(up) for p in pts]
 delta=right*((max(xs)+min(xs))/2-camera.location.dot(right))+up*((max(ys)+min(ys))/2-camera.location.dot(up));camera.location+=delta
 camera.data.ortho_scale=max(max(xs)-min(xs),(max(ys)-min(ys))*scene.render.resolution_x/scene.render.resolution_y)*1.15
views=[('01-exterior',(-7,-14,10),(5,0,0),15.8,'exterior'),('02-habitation-cutaway',(-7,-14,8),(5,0,0),15.8,'cutaway'),('03-engineering-cutaway',(-5,-13,8),(4.8,0,-.3),14.7,'systems'),('04-side-profile',(5,-22,0),(5,0,0),13.5,'side'),('05-thermal-subsystems',(5,-10,6),(5,-.7,-.8),7.5,'thermal')]
for name,pos,target,scale,mode in views:
 for ob in objects:
  g=ob['group'];hide=False
  if mode in ['cutaway','systems'] and ob['cutaway_hide']:hide=True
  if mode=='systems' and g in ['habitation','solar']:hide=True
  if mode=='thermal' and g not in ['thermal','avionics','power','routes']:hide=True
  ob.hide_render=hide
 brand.hide_render=mode!='exterior' and mode!='side'
 look(pos,target,scale);fit_visible();scene.render.filepath=str(B/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
for ob in objects:ob.hide_render=False
brand.hide_render=False;look((-7,-14,10),(5,0,0),15.8);fit_visible()
bpy.ops.wm.save_as_mainfile(filepath=str(B/'cad/Haven1_Public_Reference_R1.blend'))
(B/'verification/blender-verification.json').write_text(json.dumps({'blender_version':bpy.app.version_string,'host':'Intel','mesh_objects':len(objects),'glb_exported':True,'rendered_views':[v[0] for v in views],'render_engine':'Cycles CPU','render_threads':8,'physics_solved':False},indent=2))
