import * as THREE from './source/vendor/three.module.js';
import {OrbitControls} from './source/vendor/OrbitControls.js';
const base='.';
const $=s=>document.querySelector(s),root=$('#haps-viewer');
const pretty=(v,n=2)=>Number(v).toFixed(n);
let ready=false;
function rejection(){
 const ids=['load','temperature','h','alpha','epsilon'];const x=Object.fromEntries(ids.map(k=>[k,Number($('#haps-'+k).value)]));
 if(ids.some(k=>!$('#haps-'+k).value||!$('#haps-'+k).validity.valid)){ $('#haps-screen-result').textContent='Enter values within the displayed limits.';return;}
 const shaded=$('#haps-sun').value==='shaded',T=x.temperature+273.15,Ta=216.65,sigma=5.670374419e-8;
 const conv=x.h*(T-Ta),emission=x.epsilon*sigma*T**4,IR=x.epsilon*(.2*240+.4*80+.4*sigma*253.15**4),solar=shaded?0:x.alpha*1361*.7;
 const net=conv+emission-IR-solar;
 $('#haps-screen-result').textContent=`Net rejection: ${pretty(net)} W/m². ${net>0?`Isothermal effective area for ${pretty(x.load,0)} W: ${pretty(x.load/net,3)} m².`:'No positive rejection under these assumed conditions; this surface cannot carry the selected load.'} Algebraic screen only.`;
 $('#haps-screen-terms').textContent=`Outward convection ${pretty(conv)} + IR emission ${pretty(emission)} − absorbed Earth/sky/hull IR ${pretty(IR)} − direct solar ${pretty(solar)} = ${pretty(net)} W/m². Reflected solar, spreading/contact losses and time dependence are excluded.`;
}
for(const id of ['load','temperature','h','alpha','epsilon','sun'])$('#haps-'+id)?.addEventListener('input',rejection);if($('#haps-screen-result'))rejection();
const photo=$('#haps-reference'),photoData={flight:['sceye-2024-flight.jpg','Sceye · August 2024 flight photograph','https://sceye.com/press-releases/the-future-of-non-terrestrial-infrastructure-sceye-demonstrates-breakthrough-diurnal-flight-in-the-stratosphere-with-renewable-energy/'],profile:['softbank-profile.webp','SoftBank · published 65 m reference profile','https://www.softbank.jp/corp/philosophy/technology/special/ntn-solution/haps/'],crown:['mobius-bench.jpg','Mobius gallery · dorsal solar-array view','https://www.mobiusrobotics.com/sceye'],oblique:['mobius-inflight.png','Mobius gallery · complementary exterior view','https://www.mobiusrobotics.com/sceye'],patent:['patent-harness.png','Historical harness patent · side-propeller concept, not current stern layout','https://patents.google.com/patent/US20190329855A1/en']};
photo?.addEventListener('change',()=>{const [file,title,url]=photoData[photo.value];$('#haps-reference-image').src='https://khanisolutions.com/assets/studies/sceye-haps/reference-images/'+file;$('#haps-reference-image').alt=title;$('#haps-reference-caption').textContent=title+'. Publisher image, retained as a visual reference; not a dimensioned drawing.';$('#haps-reference-link').href=url;});
for(const button of document.querySelectorAll('[data-haps-view-image]'))button.addEventListener('click',()=>{const mode=button.dataset.hapsViewImage;$('#haps-cad-image').src=base+'/review/'+mode+'.png';$('#haps-cad-image-link').href=base+'/review/'+mode+'.png';$('#haps-cad-image').alt='Native FreeCAD '+mode.replaceAll('-',' ')+'; independent reference reconstruction';for(const b of document.querySelectorAll('[data-haps-view-image]'))b.setAttribute('aria-pressed',String(b===button));});
if(root){
 try{
 const responses=await Promise.all([fetch(base+'/cad/vehicle-mesh.json'),fetch(base+'/cad/components.json'),fetch(base+'/inputs/sources.json')]);if(responses.some(r=>!r.ok))throw Error('CAD data could not be loaded');
 const [data,records,sources]=await Promise.all(responses.map(r=>r.json()));const recs=new Map(records.map(r=>[r.tag,r])),sourceMap=new Map(sources.map(r=>[r.id,r]));
 const select=$('#haps-part'),mode=$('#haps-mode');let selected='HULL';
 for(const r of records.filter(r=>!r.tag.startsWith('PV')||r.tag==='PV0000')){const option=document.createElement('option');option.value=r.tag;option.textContent=r.tag+' · '+r.label;select.append(option);}
 function details(tag){if(tag.startsWith('PV'))tag='PV0000';selected=tag;const r=recs.get(tag);if(!r)return;if([...select.options].some(o=>o.value===tag))select.value=tag;
 $('#haps-part-title').textContent=r.tag+' · '+r.label;$('#haps-part-evidence').textContent=r.evidence+' · geometry status';$('#haps-part-concern').textContent=r.thermal_concern;$('#haps-part-scope').textContent=r.geometry_scope;
 const links=r.source_ids.map(k=>{const a=document.createElement('a'),s=sourceMap.get(k);a.textContent=k;a.href=s?.url.startsWith('http')?s.url:base+'/docs/Design-Basis.txt';a.target='_blank';a.rel='noopener';return a;});$('#haps-part-sources').replaceChildren(...links);
 for(const m of meshes){m.material.emissive.setHex(m.userData.tag===tag?0x17384b:0x000000);m.material.emissiveIntensity=m.userData.tag===tag?.35:0;}
 }
 const canvas=$('#haps-canvas'),renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0xeaf3f6);renderer.outputColorSpace=THREE.SRGBColorSpace;
 const scene=new THREE.Scene();scene.add(new THREE.HemisphereLight(0xffffff,0x56697c,2.4));const a=new THREE.DirectionalLight(0xffffff,3);a.position.set(-20,-40,70);scene.add(a);const b=new THREE.DirectionalLight(0xc7e1ff,1.5);b.position.set(80,30,10);scene.add(b);
 const camera=new THREE.OrthographicCamera(-40,40,25,-25,.01,2000);camera.up.set(0,0,1);const controls=new OrbitControls(camera,canvas);controls.enableDamping=true;controls.dampingFactor=.12;controls.minZoom=.15;controls.maxZoom=150;
 const meshes=[];
 for(const item of data.objects){const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(item.positions.flat(),3));geo.setIndex(item.triangles.flat());geo.computeVertexNormals();const color=new THREE.Color(...item.color);const mat=new THREE.MeshStandardMaterial({color,metalness:item.group==='exterior'?.38:.12,roughness:.55,side:THREE.DoubleSide});const m=new THREE.Mesh(geo,mat);m.userData=item;scene.add(m);meshes.push(m);}
 function selectedSet(m){return selected.startsWith('PV')?m.userData.tag.startsWith('PV'):m.userData.tag===selected;}
 function visibleBounds(){const box=new THREE.Box3();for(const m of meshes)if(m.visible)box.expandByObject(m);return box;}
 function fit(){const box=visibleBounds();if(box.isEmpty())return;const center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());const scale=Math.max(size.length(),1),view=mode.value;
 const direction=view==='top'?new THREE.Vector3(0,0,1):view==='side'?new THREE.Vector3(0,-1,0):new THREE.Vector3(-.75,-1,.55).normalize();camera.up.set(0,0,1);if(view==='top')camera.up.set(1,0,0);
 camera.position.copy(center).addScaledVector(direction,scale*2);controls.target.copy(center);camera.lookAt(center);camera.updateMatrixWorld(true);
 let xmax=0,ymax=0;for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){const p=new THREE.Vector3(x,y,z).applyMatrix4(camera.matrixWorldInverse);xmax=Math.max(xmax,Math.abs(p.x));ymax=Math.max(ymax,Math.abs(p.y));}
 const aspect=canvas.clientWidth/canvas.clientHeight,halfH=Math.max(ymax,xmax/aspect,.3)*1.18;camera.left=-halfH*aspect;camera.right=halfH*aspect;camera.top=halfH;camera.bottom=-halfH;camera.zoom=1;camera.updateProjectionMatrix();controls.update();
 }
 function setMode(){const v=mode.value,thermal=$('#haps-proposal').checked;
 for(const m of meshes){const d=m.userData;let show=d.special!=='cutaway';
 if(v==='cutaway')show=d.special!=='full_hull'&&d.special!=='cover';
 if(v==='systems')show=d.special!=='cover'&&!['exterior','solar','propulsion'].includes(d.group)&&!['ESC','TC5'].includes(d.tag);
 if(v==='stern')show=['MOTOR','SHAFT','SPINNER','ESC','PROP0','PROP1','PROP2'].includes(d.tag);
 if(v==='focus')show=selectedSet(m);
 if(!thermal&&['proposal','sensor'].includes(d.group))show=false;
 m.visible=show;m.material.transparent=d.tag==='HULL'&&Number($('#haps-opacity').value)<100;m.material.opacity=d.tag==='HULL'?Number($('#haps-opacity').value)/100:1;m.material.depthWrite=!m.material.transparent;}
 fit();root.dataset.view=v;$('#haps-view-status').textContent=`${meshes.filter(m=>m.visible).length} visible display objects · ${v==='focus'?'selected '+selected:v} view · subsystem colors, no solved temperature field.`;
 }
 mode.addEventListener('change',()=>{setMode();const v=mode.value;if(v!=='focus'&&!meshes.some(m=>m.visible&&selectedSet(m)))details(v==='systems'?'AVBASE':v==='stern'?'MOTOR':v==='cutaway'?'BAT0':'HULL');});$('#haps-proposal').addEventListener('change',setMode);$('#haps-opacity').addEventListener('input',()=>{for(const m of meshes)if(m.userData.tag==='HULL'){m.material.opacity=Number($('#haps-opacity').value)/100;m.material.transparent=m.material.opacity<1;m.material.depthWrite=!m.material.transparent;}});
 select.addEventListener('change',()=>{details(select.value);if(mode.value==='focus'){if(['proposal','sensor'].includes(recs.get(selected)?.subsystem))$('#haps-proposal').checked=true;setMode();}});$('#haps-focus').addEventListener('click',()=>{mode.value='focus';if(['proposal','sensor'].includes(recs.get(selected)?.subsystem))$('#haps-proposal').checked=true;setMode();});$('#haps-reset').addEventListener('click',()=>{mode.value='overview';setMode();});
 const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let down;
 canvas.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});canvas.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;const r=canvas.getBoundingClientRect();pointer.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(meshes.filter(m=>m.visible));if(hit[0])details(hit[0].object.userData.tag);});
 new ResizeObserver(()=>{const w=canvas.clientWidth,h=canvas.clientHeight;renderer.setSize(w,h,false);fit();}).observe(canvas);
 details('HULL');setMode();renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});ready=true;root.dataset.ready='true';$('#haps-static-fallback').hidden=true;
 }catch(error){$('#haps-view-status').textContent='The interactive 3D view is unavailable here. Native CAD views and all downloads remain available below.';$('#haps-canvas').hidden=true;$('#haps-static-fallback').hidden=false;root.dataset.ready='fallback';console.error(error);}
}
