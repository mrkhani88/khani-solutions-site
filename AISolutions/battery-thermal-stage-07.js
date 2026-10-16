/* Stored conservative layered solutions. Colors are quantitative FV values. */
(() => {
'use strict';
const base='/assets/studies/battery-thermal/stage-07', el=id=>document.getElementById(id);
const canvas=el('thermal-scene');
let data, cad, surfaces, palette, gl, program, posAttr, colAttr, matrixUniform, offsetUniform;
let objects=[], mapCards=[], mode='part', az=-.18, elevation=1.12, zoom=1, drag=null, timer=null, lastRange=null;
const offsets={Display:-24,Midplate:-12,Frame:0,Battery:8,MainPCB:8,RFPCB:20,BackGlass:58,RFPad:28,GraphiteSpreader:38,SpreaderAdhesive:48,U01:8,U02:8,U03:8,U04:8,U05:8,U06:20,U07:20};
const getFrame=()=>Math.round(+el('thermal-time').value/30);
const getCase=()=>data.cases[el('thermal-case').value];
const getSelected=()=>el('thermal-component').value;
function stats(name=getSelected(),caseId=el('thermal-case').value) {
  const c=data.cases[caseId].components[name];if(!c)return null;
  const field=data.cases[caseId].values, start=getFrame()*data.cases[caseId].mesh_nodes;
  let min=Infinity,max=-Infinity,sum=0,weight=0;
  c.indices.forEach((i,k)=>{const t=field[start+i],w=c.weights_J_K[k];min=Math.min(min,t);max=Math.max(max,t);sum+=w*t;weight+=w;});
  return {min,mean:sum/weight,max};
}
function color(t,low,high){return palette[Math.max(0,Math.min(255,Math.round((t-low)/(high-low)*255)))];}
function compile(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
function setup(){
  gl=canvas.getContext('webgl',{antialias:true,preserveDrawingBuffer:true});
  if(!gl)throw Error('WebGL is unavailable. The static maps and ParaView downloads show the same solved fields.');
  program=gl.createProgram();
  gl.attachShader(program,compile(gl.VERTEX_SHADER,'attribute vec3 pos;attribute vec3 col;uniform mat4 camera;uniform float offsetZ;varying vec3 c;void main(){gl_Position=camera*vec4(pos+vec3(0.0,0.0,offsetZ),1.0);c=col;}'));
  gl.attachShader(program,compile(gl.FRAGMENT_SHADER,'precision mediump float;varying vec3 c;void main(){gl_FragColor=vec4(c,1.0);}'));
  gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
  posAttr=gl.getAttribLocation(program,'pos');colAttr=gl.getAttribLocation(program,'col');matrixUniform=gl.getUniformLocation(program,'camera');offsetUniform=gl.getUniformLocation(program,'offsetZ');
  gl.enableVertexAttribArray(posAttr);gl.enableVertexAttribArray(colAttr);gl.enable(gl.DEPTH_TEST);
  for(const [caseId,config] of Object.entries(data.cases)){
  const thermal=new Map(config.surfaces.map(o=>[o.id,o]));
  for(const part of config.cad){
    const shape=thermal.get(part.id)||part, component=config.components[part.id], vertices=[], indices=[], gray=[];
    const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
    for(const tri of shape.triangles){
      const a=shape.vertices[tri[0]],b=shape.vertices[tri[1]],c=shape.vertices[tri[2]];
      const u=b.map((x,i)=>x-a[i]),v=c.map((x,i)=>x-a[i]),n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
      const shade=.65+.25*Math.abs((n[0]*.25-n[1]*.35+n[2]*.9)/(Math.hypot(...n)||1));
      for(const j of tri){const p=shape.vertices[j];vertices.push(...p);p.forEach((x,i)=>{lo[i]=Math.min(lo[i],x);hi[i]=Math.max(hi[i],x);});if(component)indices.push(shape.node_indices?shape.node_indices[j]:component.indices[0]);else gray.push(.57*shade,.59*shade,.61*shade);}
    }
    const posBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,posBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);
    const colors=new Float32Array(vertices.length),colBuffer=gl.createBuffer();if(!component)colors.set(gray);
    gl.bindBuffer(gl.ARRAY_BUFFER,colBuffer);gl.bufferData(gl.ARRAY_BUFFER,colors,gl.DYNAMIC_DRAW);
    let gridBuffer=null,gridCount=0;
    if(shape.grid_vertices){gridBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,gridBuffer);const grid=new Float32Array(shape.grid_vertices.flat());gridCount=grid.length/3;gl.bufferData(gl.ARRAY_BUFFER,grid,gl.STATIC_DRAW);}
    objects.push({id:part.id,label:part.label,visible:part.visible,variant:caseId,solved:!!component,posBuffer,colBuffer,colors,indices,lo,hi,count:vertices.length/3,gridBuffer,gridCount,colorKey:null});
    if(component&&caseId==='reference'){
      const card=document.createElement('div');card.className='map-card';const title=document.createElement('h3');title.textContent=part.id;card.append(title);
      const pair=document.createElement('div');pair.className='map-pair';card.append(pair);
      const beforeCanvas=document.createElement('canvas'),mapCanvas=document.createElement('canvas');
      for(const [label,c] of [['25 µm',beforeCanvas],['Selected adhesive',mapCanvas]]){const item=document.createElement('div'),heading=document.createElement('span');heading.textContent=label;item.append(heading);c.width=280;c.height=280;c.setAttribute('aria-label',part.id+' '+label.toLowerCase()+' temperature map');item.append(c);pair.append(item);}
      const readout=document.createElement('p');readout.className='small';card.append(readout);el('component-map-gallery').append(card);
      mapCards.push({id:part.id,shape,component,lo,hi,canvas:mapCanvas,beforeCanvas,readout,card});
    }
  }
  }
  mapCards.sort((a,b)=>data.metadata.component_order.indexOf(a.id)-data.metadata.component_order.indexOf(b.id));
  for(const card of mapCards)el('component-map-gallery').append(card.card);
}
function active(){
  const caseId=el('thermal-case').value;
  const eligible=objects.filter(o=>o.variant===caseId);
  if(mode==='part')return eligible.filter(o=>o.id===getSelected());
  if(mode==='layers')return eligible.filter(o=>o.solved);
  return eligible.filter(o=>!['Display','BackGlass','GraphiteSpreader','SpreaderAdhesive'].includes(o.id)&&(o.solved||(el('show-context').checked&&o.visible)));
}
function draw(){
  if(!gl||!data)return;
  const r=canvas.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(r.width*dpr);canvas.height=Math.round(r.height*dpr);
  gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(.933,.953,.969,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
  const s=stats(),lohi=data.metadata.shared_color_range_C.slice();
  if(el('focus-scale').checked&&s){lohi[0]=Math.floor(s.min*10)/10;lohi[1]=Math.ceil(s.max*10)/10;if(lohi[1]-lohi[0]<.1){lohi[0]=s.mean-.5;lohi[1]=s.mean+.5;}}
  const [low,high]=lohi;lastRange=lohi;
  const ca=Math.cos(az),sa=Math.sin(az),se=Math.sin(elevation),ce=Math.cos(elevation);
  const project=([x,y,z])=>[ca*x-sa*y,(sa*x+ca*y)*se+z*ce,-(sa*x+ca*y)*ce+z*se];
  const parts=active(),lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
  for(const o of (parts.length?parts:objects.filter(o=>o.id===getSelected()))){let dz=mode==='layers'?(offsets[o.id]||0):0;for(const x of [o.lo[0],o.hi[0]])for(const y of [o.lo[1],o.hi[1]])for(const z of [o.lo[2],o.hi[2]])project([x,y,z+dz]).forEach((q,i)=>{lo[i]=Math.min(lo[i],q);hi[i]=Math.max(hi[i],q);});}

  const scale=Math.min((r.width-60)/Math.max(.1,hi[0]-lo[0]),(r.height-65)/Math.max(.1,hi[1]-lo[1]))*zoom;
  const sx=2*scale/r.width,sy=2*scale/r.height,zr=Math.max(1,(hi[2]-lo[2])*.65),cx=(lo[0]+hi[0])/2,cy=(lo[1]+hi[1])/2,cz=(lo[2]+hi[2])/2;
  const camera=new Float32Array([sx*ca,sy*sa*se,sa*ce/zr,0,-sx*sa,sy*ca*se,ca*ce/zr,0,0,sy*ce,-se/zr,0,-sx*cx,-sy*cy,cz/zr,1]);
  gl.uniformMatrix4fv(matrixUniform,false,camera);
  const colorKey=[el('thermal-case').value,getFrame(),low,high].join(':');
  for(const o of parts){
    gl.uniform1f(offsetUniform,mode==='layers'?(offsets[o.id]||0):0);
    if(o.solved&&o.colorKey!==colorKey){const field=getCase().values,start=getFrame()*getCase().mesh_nodes;for(let i=0;i<o.indices.length;i++)o.colors.set(color(field[start+o.indices[i]],low,high),i*3);gl.bindBuffer(gl.ARRAY_BUFFER,o.colBuffer);gl.bufferSubData(gl.ARRAY_BUFFER,0,o.colors);o.colorKey=colorKey;}
    gl.bindBuffer(gl.ARRAY_BUFFER,o.posBuffer);gl.vertexAttribPointer(posAttr,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ARRAY_BUFFER,o.colBuffer);gl.vertexAttribPointer(colAttr,3,gl.FLOAT,false,0,0);gl.enableVertexAttribArray(colAttr);gl.drawArrays(gl.TRIANGLES,0,o.count);
    if(el('show-grid').checked&&o.gridBuffer){gl.bindBuffer(gl.ARRAY_BUFFER,o.gridBuffer);gl.vertexAttribPointer(posAttr,3,gl.FLOAT,false,0,0);gl.disableVertexAttribArray(colAttr);gl.vertexAttrib3f(colAttr,.16,.19,.22);gl.drawArrays(gl.LINES,0,o.gridCount);gl.enableVertexAttribArray(colAttr);}
  }
  el('thermal-time-label').textContent=(+el('thermal-time').value/60).toFixed(1)+' min';
  el('scale-low').textContent=low.toFixed(1)+' °C';el('scale-high').textContent=high.toFixed(1)+' °C';
  el('scale-note').textContent=el('focus-scale').checked?'Range follows the selected component at this time. All visible parts share it; values outside it are clipped.':'Fixed 25–75 °C scale across all components, cases and times.';
  for(const [id,key] of [['map-min','min'],['map-mean','mean'],['map-max','max']])el(id).textContent=s?s[key].toFixed(3)+' °C':'—';
  el('component-status').textContent=s?data.components[getSelected()].kind+'. Readouts use thermal nodes; average is capacity weighted.':'This component has no independent thermal solution. Gray is context only. Supports, TIM and adhesive are represented by conductance links where specified, without their own temperatures.';
  if(getSelected()==='RFPad'&&s)el('component-status').textContent+=' Installed thickness: '+data.cases[el('thermal-case').value].pad_thickness_mm.toFixed(3)+' mm.';
  el('case-description').textContent=getCase().label+' · '+(+el('thermal-time').value<600?'Heat sources on':'Sources off; internal heat exchange continues')+' · Same 3.75 W total on-phase heat · 25 °C ambient';
  el('view-note').textContent=mode==='assembly'?'Open assembly: display, back cover and bonded spreader layers are hidden to reveal heat spreading. Their thermal effects remain in the solution.':mode==='layers'?'Exploded layers: spacing is for inspection only; it does not change any thermal contact.':'Selected component at its actual CAD scale. Spatial layers use one temperature through thickness.';
  updateTable();
  if(el('all-maps').open)drawGallery(low,high);
}
function drawGallery(low,high){
  const selected=el('thermal-case').value;
  for(const card of mapCards){
    const variants=objects.filter(o=>o.id===card.id);const lo=[0,1].map(i=>Math.min(...variants.map(o=>o.lo[i]))),hi=[0,1].map(i=>Math.max(...variants.map(o=>o.hi[i])));
    for(const [caseId,mapCanvas] of [['reference',card.beforeCanvas],[selected,card.canvas]]){
      const config=data.cases[caseId],component=config.components[card.id],field=config.values,start=getFrame()*config.mesh_nodes;
      const shape=config.surfaces.find(o=>o.id===card.id)||config.cad.find(o=>o.id===card.id),ctx=mapCanvas.getContext('2d'),s=stats(card.id,caseId);
      ctx.clearRect(0,0,280,280);const scale=Math.min(250/(hi[0]-lo[0]),250/(hi[1]-lo[1]));const cx=(lo[0]+hi[0])/2,cy=(lo[1]+hi[1])/2;
      if(component.indices.length===1){const c=color(s.mean,low,high);ctx.fillStyle='rgb('+c.map(v=>Math.round(v*255)).join(',')+')';const v=variants.find(o=>o.variant===caseId);ctx.fillRect(140+(v.lo[0]-cx)*scale,140-(v.hi[1]-cy)*scale,(v.hi[0]-v.lo[0])*scale,(v.hi[1]-v.lo[1])*scale);}
      else for(const tri of shape.triangles){
        const pts=tri.map(i=>shape.vertices[i]);if(Math.abs((pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1])-(pts[1][1]-pts[0][1])*(pts[2][0]-pts[0][0]))<1e-10)continue;
        const c=color(field[start+shape.node_indices[tri[0]]],low,high);ctx.fillStyle='rgb('+c.map(v=>Math.round(v*255)).join(',')+')';ctx.strokeStyle=ctx.fillStyle;ctx.lineWidth=.35;ctx.beginPath();pts.forEach((p,i)=>{const x=140+(p[0]-cx)*scale,y=140-(p[1]-cy)*scale;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.closePath();ctx.fill();ctx.stroke();
      }
    }
    const a=stats(card.id,'reference'),b=stats(card.id,selected);
    card.readout.textContent='Max '+a.max.toFixed(3)+' → '+b.max.toFixed(3)+' °C · Change '+(b.max-a.max).toFixed(3)+' K';
  }
  el('gallery-scale').textContent='Left: 25 µm reference. Right: '+getCase().label+' · '+(+el('thermal-time').value/60).toFixed(1)+' min · Shared '+low.toFixed(1)+'–'+high.toFixed(1)+' °C range. Each component pair uses identical spatial bounds; different components are fitted separately.';
}
function updateTable(){let html='';const selected=el('thermal-case').value;for(const name of data.metadata.component_order){const a=stats(name,'reference'),b=stats(name,selected);html+='<tr><th scope="row">'+name+'</th><td>'+a.max.toFixed(3)+'</td><td>'+b.max.toFixed(3)+'</td><td>'+(b.max-a.max).toFixed(3)+'</td><td>'+a.mean.toFixed(3)+' → '+b.mean.toFixed(3)+'</td></tr>';}el('component-values').innerHTML=html;el('selected-column').textContent=getCase().label+' max (°C)';}
function pause(){clearInterval(timer);timer=null;el('thermal-play').textContent='Play';}
function setMode(value){mode=value;for(const [id,m] of [['view-part','part'],['view-assembly','assembly'],['view-layers','layers']])el(id).setAttribute('aria-pressed',String(m===value));zoom=1;if(value==='layers'){az=-.32;elevation=.70;}draw();}
function reset(){az=-.18;elevation=1.12;zoom=1;draw();}
async function json(url){const r=await fetch(url);if(!r.ok)throw Error('Result file failed: '+r.status);return r.json();}
async function init(){try{
  [data,palette]=await Promise.all(['viewer_data.json','palette.json'].map(f=>json(base+'/results/'+f)));
  await Promise.all(Object.values(data.cases).map(async c=>{
    const r=await fetch(base+'/results/'+c.field_file);if(!r.ok)throw Error('Temperature field failed: '+r.status);const buffer=await r.arrayBuffer();c.values=new Float32Array(buffer);if(c.values.length!==c.shape[0]*c.shape[1])throw Error('Temperature field shape mismatch');
    [c.surfaces,c.cad]=await Promise.all([c.surface_file,c.assembly_file].map(f=>json(base+'/results/'+f)));
  }));cad=data.cases.reference.cad;
  setup();for(const o of cad){const option=document.createElement('option');option.value=o.id;option.textContent=(o.id==='RFPad'?'RF pad · thickness follows adhesive':o.id==='GraphiteSpreader'?'Graphite sheet · 50 × 70 mm footprint':o.id==='SpreaderAdhesive'?'Bond adhesive · 50 × 70 mm footprint':o.id==='BackGlass'?'Back cover · temperature field':o.label)+(data.components[o.id]?' · SOLVED':' · context');el('thermal-component').append(option);}el('thermal-component').value='BackGlass';
  el('color-legend').style.background='linear-gradient(to right,'+palette.filter((_,i)=>i%16===0||i===255).map(c=>'rgb('+c.map(v=>Math.round(v*255)).join(',')+')').join(',')+')';
  for(const id of ['thermal-case','thermal-component'])el(id).onchange=()=>{pause();draw();};
  el('view-part').onclick=()=>setMode('part');el('view-assembly').onclick=()=>setMode('assembly');el('view-layers').onclick=()=>setMode('layers');
  el('camera-iso').onclick=reset;el('camera-reset').onclick=reset;el('camera-top').onclick=()=>{az=0;elevation=Math.PI/2;zoom=1;draw();};
  for(const id of ['show-grid','show-context','focus-scale'])el(id).onchange=draw;
  el('all-maps').ontoggle=draw;
  el('thermal-time').oninput=()=>{pause();draw();};el('thermal-heat-off').onclick=()=>{pause();el('thermal-time').value=600;draw();};el('thermal-start').onclick=()=>{pause();el('thermal-time').value=0;draw();};
  el('thermal-play').onclick=()=>{if(timer){pause();return;}if(+el('thermal-time').value>=1800)el('thermal-time').value=0;el('thermal-play').textContent='Pause';timer=setInterval(()=>{el('thermal-time').value=Math.min(1800,+el('thermal-time').value+30);draw();if(+el('thermal-time').value===1800)pause();},180);};
  canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(!drag)return;az+=(e.clientX-drag[0])*.008;elevation=Math.max(-1.55,Math.min(1.57,elevation+(e.clientY-drag[1])*.008));drag=[e.clientX,e.clientY];draw();};canvas.onpointerup=()=>drag=null;canvas.onpointercancel=()=>drag=null;
  canvas.onwheel=e=>{e.preventDefault();zoom=Math.max(.5,Math.min(3,zoom*Math.exp(-e.deltaY*.001)));draw();};canvas.ondblclick=reset;new ResizeObserver(draw).observe(canvas);
  el('load-status').textContent='3 adhesive thicknesses · 17 solved components in every case · 61 saved times · independent meshes';
  draw();window.THERMAL_STAGE7={data,getStats:stats,get frame(){return getFrame();},get range(){return lastRange;},get selected(){return getSelected();},get caseId(){return el('thermal-case').value;},get webglError(){return gl.getError();},get mode(){return mode;},get activeIds(){return active().map(o=>o.id);},get geometryInfo(){return active().map(o=>({id:o.id,lo:o.lo,hi:o.hi}));},get camera(){return {az,elevation,zoom};}};
}catch(e){el('load-status').textContent=e.message;el('load-status').className='error';console.error(e);}}
init();
})();
