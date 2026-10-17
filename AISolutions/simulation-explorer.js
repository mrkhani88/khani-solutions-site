/* Static native-result inspection. Controls never synthesize or solve fields. */
(async()=>{
const root=document.querySelector('[data-explorer]');if(!root)return;
const el=k=>root.querySelector(`[data-${k}]`),set=(k,t)=>el(k).textContent=t;
let timer=null,config,view,fields,index=0,variable=0,part='all',selected=-1,chartChoice='0',zoom=1,pan=[0,0],paths=[],boxes=[],transform;
const canvas=el('map'),ctx=canvas.getContext('2d'),chart=el('chart'),cc=chart.getContext('2d');
const fmt=(x,d=3)=>Number.isFinite(x)?Number(x).toLocaleString(undefined,{maximumFractionDigits:d}):'—';
const nearest=(a,t)=>{let lo=0,hi=a.length-1;while(lo<hi){const m=(lo+hi)>>1;if(a[m]<t)lo=m+1;else hi=m;}return lo>0&&Math.abs(a[lo-1]-t)<Math.abs(a[lo]-t)?lo-1:lo;};
const stop=()=>{clearInterval(timer);timer=null;set('play','Play saved states');el('play').setAttribute('aria-pressed','false');};
function option(sel,value,text){const o=document.createElement('option');o.value=value;o.textContent=text;sel.append(o);}
function metric(label,value){const d=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;d.append(dt,dd);el('metrics').append(d);}
const color=v=>config.palette[Math.max(0,Math.min(255,Math.round(v*255)))];
const rgb=c=>`rgb(${c.join(',')})`;
function currentArray(){const n=view.polygons.length,q=config.variables[variable],k=q.field_index??variable;const off=(index*(config.quantity_count??config.variables.length)+k)*n;return fields.subarray(off,off+n);}
function visible(i){return part==='all'||String(view.components?.[i])===part;}
function fieldRange(a){let lo=Infinity,hi=-Infinity,n=0;for(let i=0;i<a.length;i++)if(visible(i)){lo=Math.min(lo,a[i]);hi=Math.max(hi,a[i]);n++;}return [lo,hi,n];}
function buildPaths(){paths=view.polygons.map(poly=>{const p=new Path2D();poly.forEach(([x,y],i)=>i?p.lineTo(x,y):p.moveTo(x,y));p.closePath();return p;});boxes=view.polygons.map(p=>[Math.min(...p.map(x=>x[0])),Math.max(...p.map(x=>x[0])),Math.min(...p.map(x=>x[1])),Math.max(...p.map(x=>x[1]))]);}
function drawMap(){
 if(config.mode==='images')return;
 const w=canvas.width,h=canvas.height,bb=view.bounds??[Math.min(...boxes.map(b=>b[0])),Math.max(...boxes.map(b=>b[1])),Math.min(...boxes.map(b=>b[2])),Math.max(...boxes.map(b=>b[3]))];
 const scale=Math.min((w-110)/(bb[1]-bb[0]),(h-100)/(bb[3]-bb[2]))*zoom,ox=w/2-scale*(bb[0]+bb[1])/2+pan[0],oy=h/2+scale*(bb[2]+bb[3])/2+pan[1];transform={scale,ox,oy};
 ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#f1f5f6';ctx.fillRect(0,0,w,h);ctx.save();ctx.beginPath();ctx.rect(45,20,w-60,h-60);ctx.clip();ctx.setTransform(scale,0,0,-scale,ox,oy);
 const vals=currentArray(),q=config.variables[variable],lo=q.range[0],range=q.range[1]-lo;ctx.lineWidth=.4/scale;
 for(let i=0;i<paths.length;i++){
  const b=boxes[i];if(ox+scale*b[1]<45||ox+scale*b[0]>w-15||oy-scale*b[3]>h-40||oy-scale*b[2]<20)continue;
  ctx.fillStyle=visible(i)?rgb(color((vals[i]-lo)/range)):'#cdd7dc';ctx.fill(paths[i]);
  if(el('mesh').value==='on'){ctx.strokeStyle='#213d4e66';ctx.stroke(paths[i]);}
 }
 if(selected>=0&&visible(selected)){ctx.lineWidth=2/scale;ctx.strokeStyle='#ff4e42';ctx.stroke(paths[selected]);}
 ctx.restore();ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#254353';ctx.font=`${12*canvas.width/(canvas.getBoundingClientRect().width||canvas.width)}px system-ui`;ctx.textAlign='left';ctx.fillText(view.axis_labels[0],w-110,h-8);ctx.fillText(view.axis_labels[1],10,18);
 // Physical coordinate ticks follow the current pan/zoom.
 ctx.font=`${11*canvas.width/(canvas.getBoundingClientRect().width||canvas.width)}px system-ui`;for(let i=0;i<=4;i++){let x=60+i*(w-100)/4;ctx.textAlign='center';ctx.fillText(fmt((x-ox)/scale,2),x,h-25);let y=45+i*(h-110)/4;ctx.textAlign='left';ctx.fillText(fmt((oy-y)/scale,2),3,y);}
}
function chartSeries(){if(chartChoice==='probe'&&selected>=0){const n=view.polygons.length,k=config.variables[variable].field_index??variable,qc=config.quantity_count??config.variables.length;return {time:config.snapshots.map(s=>s.time),values:config.snapshots.map((s,j)=>fields[(j*qc+k)*n+selected]),label:`Local displayed cell ${selected}`,unit:config.variables[variable].unit};}
 const h=chartChoice.startsWith('s')?config.secondary_history:config.history,k=Number(chartChoice.replace(/^s/,''));return {...h.series[k],time:h.time};}
function drawChart(){const s=chartSeries(),w=chart.width,h=chart.height,L=95,R=w-25,T=32,B=h-65;let lo=Math.min(...s.values),hi=Math.max(...s.values);const pad=(hi-lo)*.08||Math.max(1,Math.abs(hi)*.03);lo-=pad;hi+=pad;const a=s.time[0],b=s.time.at(-1),xp=t=>L+(t-a)/(b-a||1)*(R-L),yp=v=>B-(v-lo)/(hi-lo)*(B-T);cc.fillStyle='#101f30';cc.fillRect(0,0,w,h);cc.font=`${12*chart.width/(chart.getBoundingClientRect().width||chart.width)}px system-ui`;cc.textAlign='right';for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,y=yp(v);cc.strokeStyle='#385064';cc.beginPath();cc.moveTo(L,y);cc.lineTo(R,y);cc.stroke();cc.fillStyle='#b7ccd9';cc.fillText(fmt(v,2),L-12,y+5);}cc.textAlign='center';for(let i=0;i<=4;i++){let t=a+(b-a)*i/4;cc.fillText(fmt(t,3),xp(t),B+30);}cc.fillText('Saved simulation time / s',(L+R)/2,h-8);cc.textAlign='left';cc.fillText(s.unit,L,T-10);cc.strokeStyle='#79e0d5';cc.lineWidth=2;cc.beginPath();s.time.forEach((t,i)=>i?cc.lineTo(xp(t),yp(s.values[i])):cc.moveTo(xp(t),yp(s.values[i])));cc.stroke();const t=config.snapshots[index].time,j=nearest(s.time,t);cc.strokeStyle='#ffd390';cc.beginPath();cc.moveTo(xp(t),T);cc.lineTo(xp(t),B);cc.stroke();cc.fillStyle='#ffd390';cc.beginPath();cc.arc(xp(s.time[j]),yp(s.values[j]),5,0,Math.PI*2);cc.fill();set('chart-value',`${s.label}: ${fmt(s.values[j],5)} ${s.unit} · nearest source record t = ${fmt(s.time[j],7)} s. Field t = ${fmt(t,7)} s.`);chart.dataset.value=String(s.values[j]);chart.dataset.sourceTime=String(s.time[j]);}
function render(){
 const snap=config.snapshots[index];el('time').value=index;set('stamp',`t = ${fmt(snap.time,6)} s · ${index+1}/${config.snapshots.length}`);set('phase-name',snap.phase);el('phase').value=snap.phase;
 el('metrics').replaceChildren();metric('Saved field time',`${fmt(snap.time,6)} s`);
 if(config.mode==='cells'){
  const vals=currentArray(),q=config.variables[variable],[lo,hi,n]=fieldRange(vals);set('low',fmt(q.range[0]));set('high',fmt(q.range[1]));set('unit',q.unit);metric('Displayed selection minimum',`${fmt(lo)} ${q.unit}`);metric('Displayed selection maximum',`${fmt(hi)} ${q.unit}`);
  metric('Displayed cells in selection',fmt(n,0));const eps=1e-6*Math.max(1,...q.range.map(Math.abs));let clipped=0;for(let j=0;j<vals.length;j++)if(visible(j)&&(vals[j]<q.range[0]-eps||vals[j]>q.range[1]+eps))clipped++;metric('Cells beyond color range',fmt(clipped,0));set('field-note',config.field_note+` Clipping counts ignore rounding within ${eps.toPrecision(2)} ${q.unit} of the endpoints.`);if(selected>=0)metric(`Cell ${selected}`,`${fmt(vals[selected],5)} ${q.unit}`);drawMap();root.dataset.fieldMin=lo;root.dataset.fieldMax=hi;
 }else{
  const im=el('field-image'),url=new URL(snap.image,root.dataset.url.startsWith('/')?location.origin+root.dataset.url:new URL(root.dataset.url,location.href)).href;im.src=url;im.alt=`Native wake field at ${snap.time} seconds: lift traction and Q surfaces.`;snap.circulation.forEach((g,i)=>metric(['Γ · X6 left','Γ · X6 right','Γ · X10 left','Γ · X10 right'][i],`${fmt(g)} m²/s`));
 }
 drawChart();root.dataset.index=index;root.dataset.time=snap.time;
}
function selectIndex(i){index=Math.max(0,Math.min(config.snapshots.length-1,Number(i)));render();}
async function setView(i){stop();view=config.views[i];selected=-1;zoom=1;pan=[0,0];set('load','Loading retained field values…');const res=await fetch(new URL(view.file,new URL(root.dataset.url,location.href)));if(!res.ok)throw Error(`Field download failed: ${res.status}`);const b=await res.arrayBuffer();fields=new Float32Array(b);const expected=config.snapshots.length*(config.quantity_count??config.variables.length)*view.polygons.length;if(fields.length!==expected)throw Error('Field/geometry length mismatch');buildPaths();el('part').replaceChildren();option(el('part'),'all','All materials');Object.entries(view.component_labels??{}).forEach(([k,v])=>option(el('part'),k,v));part='all';el('part-label').hidden=!view.components;set('load','Ready · retained result data');render();}
try{
 const res=await fetch(root.dataset.url);if(!res.ok)throw Error(`Data download failed: ${res.status}`);config=await res.json();index=config.default_index??0;el('time').max=config.snapshots.length-1;
 [...new Set(config.snapshots.map(s=>s.phase))].forEach(p=>option(el('phase'),p,p));el('phase-label').hidden=new Set(config.snapshots.map(s=>s.phase)).size<2;
 config.history.series.forEach((s,i)=>option(el('history'),String(i),s.label));config.secondary_history?.series.forEach((s,i)=>option(el('history'),'s'+i,s.label));set('field-note',config.field_note);set('source-note',config.source_note);
 if(config.mode==='cells'){
  config.views.forEach((v,i)=>option(el('view'),i,v.label));el('view-label').hidden=config.views.length<2;config.variables.forEach((q,i)=>option(el('quantity'),i,q.label));el('quantity-label').hidden=config.variables.length<2;
  el('gradient').style.background=`linear-gradient(90deg,${config.palette.filter((_,i)=>i%32===0||i===255).map(rgb).join(',')})`;
  await setView(0);
 }else{
  for(const k of ['map','view-label','quantity-label','part-label','mesh-label','legend','map-help','reset'])el(k).hidden=true;el('field-image').hidden=false;set('load','Ready · saved native-field renders');render();
 }
 el('ui').hidden=false;
 // Match backing-store aspect to the rendered canvas so phone layouts cannot
 // stretch the physical geometry. Draw text in consistent CSS pixel sizes.
 const resize=()=>{let changed=false;for(const c of [canvas,chart]){if(c.hidden)continue;const b=c.getBoundingClientRect(),d=Math.min(2,window.devicePixelRatio||1),w=Math.round(b.width*d),h=Math.round(b.height*d);if(w>0&&h>0&&(c.width!==w||c.height!==h)){c.width=w;c.height=h;changed=true;}}if(changed){pan=[0,0];zoom=1;}render();};
 resize();let resizeFrame;const observer=new ResizeObserver(()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(resize);});observer.observe(chart);if(config.mode==='cells')observer.observe(canvas);
 el('time').addEventListener('input',()=>{stop();selectIndex(el('time').value);});el('prev').onclick=()=>{stop();selectIndex(index-1);};el('next').onclick=()=>{stop();selectIndex(index+1);};el('phase').onchange=()=>{stop();selectIndex(config.snapshots.findIndex(s=>s.phase===el('phase').value));};
 el('play').onclick=()=>{if(timer){stop();return;}if(index===config.snapshots.length-1)index=-1;set('play','Pause');el('play').setAttribute('aria-pressed','true');timer=setInterval(()=>{selectIndex(index+1);if(index===config.snapshots.length-1)stop();},350);};document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
 el('quantity').onchange=()=>{variable=Number(el('quantity').value);render();};el('view').onchange=()=>setView(Number(el('view').value)).catch(fail);el('part').onchange=()=>{part=el('part').value;if(selected>=0&&!visible(selected)){selected=-1;chartChoice='0';el('history').value='0';}render();};el('mesh').onchange=drawMap;el('reset').onclick=()=>{zoom=1;pan=[0,0];drawMap();};el('history').onchange=()=>{chartChoice=el('history').value;drawChart();};
 function point(e){const b=canvas.getBoundingClientRect();return [(e.clientX-b.left)/b.width*canvas.width,(e.clientY-b.top)/b.height*canvas.height];}
 function world(p){return [(p[0]-transform.ox)/transform.scale,(transform.oy-p[1])/transform.scale];}
 function find(p){const [x,y]=world(p);for(let i=boxes.length-1;i>=0;i--){const b=boxes[i];if(!visible(i)||x<b[0]||x>b[1]||y<b[2]||y>b[3])continue;const poly=view.polygons[i];let inside=false;for(let a=0,b=poly.length-1;a<poly.length;b=a++){const [xa,ya]=poly[a],[xb,yb]=poly[b];if(((ya>y)!==(yb>y))&&x<(xb-xa)*(y-ya)/(yb-ya)+xa)inside=!inside;}if(inside)return i;}return -1;}
 let drag=null;const pointers=new Map();let pinch=null;
 canvas.onpointerdown=e=>{if(config.mode!=='cells')return;canvas.setPointerCapture(e.pointerId);pointers.set(e.pointerId,point(e));if(pointers.size===1)drag={p:point(e),pan:[...pan],moved:false};if(pointers.size===2){const a=[...pointers.values()];pinch={distance:Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1]),zoom};drag=null;}};
 canvas.onpointermove=e=>{if(config.mode!=='cells'||!transform)return;const p=point(e);if(pointers.has(e.pointerId))pointers.set(e.pointerId,p);if(pointers.size===2&&pinch){const a=[...pointers.values()];zoom=Math.max(.5,Math.min(20,pinch.zoom*Math.hypot(a[0][0]-a[1][0],a[0][1]-a[1][1])/Math.max(1,pinch.distance)));drawMap();return;}if(drag&&pointers.has(e.pointerId)){let dx=p[0]-drag.p[0],dy=p[1]-drag.p[1];if(Math.hypot(dx,dy)>5)drag.moved=true;pan=[drag.pan[0]+dx,drag.pan[1]+dy];drawMap();return;}const j=find(p);if(j>=0){const q=config.variables[variable];set('probe',`Cell ${j} · ${fmt(currentArray()[j],5)} ${q.unit}${view.components?' · '+view.component_labels[view.components[j]]:''}`);}};
 canvas.onpointerup=e=>{if(drag&&!drag.moved&&pointers.size===1){const j=find(point(e));if(j>=0){selected=j;chartChoice='probe';if(!el('history').querySelector('[value="probe"]'))option(el('history'),'probe','Selected cell profile');el('history').value='probe';render();}}pointers.delete(e.pointerId);drag=null;pinch=null;};canvas.onpointercancel=()=>{pointers.clear();drag=null;pinch=null;};
 canvas.onwheel=e=>{if(config.mode!=='cells')return;e.preventDefault();const p=point(e),old=world(p);zoom=Math.max(.5,Math.min(20,zoom*Math.exp(-e.deltaY*.001)));drawMap();pan[0]+=p[0]-(old[0]*transform.scale+transform.ox);pan[1]+=p[1]-(-old[1]*transform.scale+transform.oy);drawMap();};canvas.ondblclick=()=>{zoom=1;pan=[0,0];drawMap();};
 chart.onclick=e=>{stop();const b=chart.getBoundingClientRect(),x=(e.clientX-b.left)/b.width*chart.width,s=chartSeries(),t=s.time[0]+Math.max(0,Math.min(1,(x-95)/(chart.width-120)))*(s.time.at(-1)-s.time[0]);selectIndex(nearest(config.snapshots.map(s=>s.time),t));};
}catch(error){fail(error);}
function fail(error){stop();set('load',`Unable to load this result: ${error.message}. Use the data downloads below or reload the page.`);el('load').classList.add('explorer-error');console.error(error);}
})();
