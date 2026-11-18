import {sanitizePose, transformPolygons} from './geometry.mjs';
import {createFieldView} from './field-view.mjs';

const demo=document.querySelector('[data-geometry-flow]');
if(demo) {
  const canvas=demo.querySelector('canvas'),view=createFieldView(canvas);
  const picker=demo.querySelector('[data-gf-shape]');
  const inputs=Object.fromEntries(['x','y','size','angle'].map(key=>[key,demo.querySelector(`[data-gf-${key}]`)]));
  const outputs=Object.fromEntries(['x','y','size','angle'].map(key=>[key,demo.querySelector(`[data-gf-${key}-value]`)]));
  const status=demo.querySelector('[data-gf-status]'),overlay=demo.querySelector('[data-gf-overlay]');
  const retry=demo.querySelector('[data-gf-retry]'),legend=demo.querySelector('[data-gf-legend]');
  const latency=demo.querySelector('[data-gf-latency]');
  const modes=[...demo.querySelectorAll('[data-gf-mode]')];
  const angleLimits={airfoil:[-20,20],car:[-15,15],plane:[-20,20],aircraft:[-20,20],human:[-12,12]};
  const shapeLabels={airfoil:'Airfoil',car:'Car silhouette',plane:'Aircraft silhouette',aircraft:'Aircraft silhouette',human:'Human silhouette'};
  let config=null,pose=null,accepted=null,worker=null,mode='streamlines';
  let revision=0,pending=null,inFlight=null,timer=0,drawFrame=0,drag=null,lastError=false;
  const format=(value,digits=2)=>Number(value).toFixed(digits).replace('-','−');
  const copy=p=>({shape:p.shape,x:p.x,y:p.y,size:p.size,angle:p.angle});
  const same=(a,b)=>a&&b&&a.shape===b.shape&&['x','y','size','angle'].every(k=>Math.abs(a[k]-b[k])<1e-7);
  function setStatus(text,state='updating') {
    status.textContent=text;demo.dataset.state=state;
    const busy=state==='loading'||state==='updating';
    canvas.setAttribute('aria-busy',String(busy));retry.hidden=state!=='error';
    overlay.hidden=state==='ready';
    overlay.textContent=state==='loading'?'Loading local flow model':state==='error'?'Pose preview · estimate unavailable':'Pose preview · updating flow';
  }
  function polygons(){return config&&pose?transformPolygons(config,pose):[];}
  function updateControls() {
    if(!pose)return;
    picker.value=pose.shape;
    const family=config.shapes.find(s=>s.id===pose.shape);
    const range=Array.isArray(family?.angle)?family.angle:family?.angleRange||angleLimits[pose.shape]||[-12,12];
    inputs.angle.min=range[0];inputs.angle.max=range[1];
    for(const key of ['x','y','size','angle']) {
      inputs[key].value=pose[key];
      const text=key==='angle'?`${pose.angle>0?'+':''}${format(pose.angle,1)}°`:format(pose[key]);
      outputs[key].value=text;
      inputs[key].setAttribute('aria-valuetext',key==='angle'?`${pose.angle} degrees clockwise`:format(pose[key]));
    }
    const name=shapeLabels[pose.shape]||family?.label||pose.shape;
    canvas.setAttribute('aria-label',`${name} flow explorer. X ${format(pose.x)}, Y ${format(pose.y)}, size ${format(pose.size)}, rotation ${format(pose.angle,1)} degrees clockwise. ${accepted&&same(accepted.pose,pose)&&accepted.id===revision?'Accepted steady model estimate.':'Pose preview while the steady estimate updates.'}`);
  }
  function updateLegend() {
    legend.hidden=mode==='streamlines';
    if(legend.hidden)return;
    const range=view.getRange(mode);
    legend.querySelector('[data-gf-field-name]').textContent=mode==='pressure'?'Pressure coefficient Cp':'Speed |u| / U∞';
    legend.querySelector('[data-gf-field-min]').textContent=range?format(range[0],2):'—';
    legend.querySelector('[data-gf-field-max]').textContent=range?format(range[1],2):'—';
    legend.dataset.mode=mode;
    legend.title='Range follows the accepted fluid field (2nd–98th percentiles; outer values saturated). Pressure zero is neutral. Compare the numeric limits across poses.';
  }
  function draw() {
    drawFrame=0;
    const current=accepted&&same(accepted.pose,pose)&&accepted.id===revision&&!lastError;
    view.draw({polygons:polygons(),mode,preview:!current,showField:Boolean(current)});
    legend.classList.toggle('geometry-flow-pending',!current);
  }
  function scheduleDraw(){if(!drawFrame)drawFrame=requestAnimationFrame(draw);}
  function fail(message) {
    lastError=true;setStatus(message,'error');latency.textContent='—';scheduleDraw();
  }
  function dispatch() {
    if(!worker||!pending||inFlight||timer)return;
    inFlight=pending;pending=null;
    worker.postMessage({id:inFlight.id,pose:copy(inFlight.pose),config});
  }
  function queue(delay=110) {
    if(!config||!pose)return;
    lastError=false;pending={id:++revision,pose:copy(pose)};
    clearTimeout(timer);timer=0;
    setStatus(accepted?'Updating the steady flow estimate…':'Loading the local model and estimating flow…',accepted?'updating':'loading');
    updateControls();scheduleDraw();
    timer=setTimeout(()=>{timer=0;dispatch();},delay);
  }
  function startWorker() {
    worker?.terminate();inFlight=null;
    if(!('Worker' in window)){fail('This browser cannot run the local flow model. Try a current browser.');return;}
    worker=new Worker(new URL('./inference-worker.mjs',import.meta.url),{type:'module'});
    worker.addEventListener('message',event=>{
      const result=event.data;
      if(!result||!Number.isInteger(result.id))return;
      if(inFlight?.id!==result.id)return;
      inFlight=null;
      if(result.id===revision) {
        if(result.error)fail('The flow estimate is unavailable. Retry the local model.');
        else {
          try {
            const n=config.nx*config.ny;
            for(const key of ['u','v','cp','mask'])if(!result[key]||result[key].length!==n)throw Error('Invalid field shape');
            if(!same(result.pose,pose))throw Error('Mismatched pose');
            const mask=result.mask;
            for(let i=0;i<n;i++)if(!mask[i]&&(!Number.isFinite(result.u[i])||!Number.isFinite(result.v[i])||!Number.isFinite(result.cp[i])))throw Error('Nonfinite fluid field');
            accepted={...result,pose:copy(result.pose)};lastError=false;view.setField(accepted,config);
            setStatus('Steady flow estimate ready.','ready');
            latency.textContent=Number.isFinite(result.elapsedMs)?`${Math.round(result.elapsedMs)} ms`:'Ready';
            updateControls();updateLegend();scheduleDraw();
          } catch(error){console.error('Geometry flow result rejected:',error);fail('The returned flow estimate could not be displayed. Please retry.');}
        }
      }
      dispatch();
    });
    worker.addEventListener('error',event=>{
      console.error('Geometry flow worker failed:',event.message);worker?.terminate();worker=null;inFlight=null;
      fail('The local flow model could not load. Retry to load the estimate.');
    });
  }
  function change(next,delay=110) {
    if(!config)return;
    try {
      const sanitized=sanitizePose(config,next);
      if(same(sanitized,pose))return;
      pose=copy(sanitized);queue(delay);
    } catch(error){console.error('Unsupported geometry pose:',error);fail('This pose is outside the model range. Reduce the size or reset the shape.');}
  }
  function reset() {
    if(!config)return;
    const midpoint=bounds=>(bounds[0]+bounds[1])/2;
    const initial=config.defaultPose||{shape:config.shapes.find(s=>s.id==='airfoil')?.id||config.shapes[0].id,x:midpoint(config.centerX),y:midpoint(config.centerY),size:midpoint(config.size),angle:0};
    pose=copy(sanitizePose(config,initial));queue(0);
  }
  picker.addEventListener('change',()=>change({...pose,shape:picker.value,angle:0},0));
  for(const key of ['x','y','size','angle'])inputs[key].addEventListener('input',()=>change({...pose,[key]:Number(inputs[key].value)}));
  demo.querySelector('[data-gf-reset]').addEventListener('click',reset);
  modes.forEach(button=>button.addEventListener('click',()=>{
    mode=button.dataset.gfMode;modes.forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    updateLegend();scheduleDraw();
  }));
  retry.addEventListener('click',()=>{if(!config){init();return;}startWorker();if(worker)queue(0);});
  canvas.addEventListener('pointerdown',event=>{
    if(!config||!pose||event.button!==0)return;
    const point=view.world(event.clientX,event.clientY);
    if(!view.hitTest(polygons(),point))return;
    event.preventDefault();canvas.focus();canvas.setPointerCapture(event.pointerId);
    drag={id:event.pointerId,start:point,pose:copy(pose)};canvas.classList.add('is-dragging');
  });
  canvas.addEventListener('pointermove',event=>{
    if(!drag||event.pointerId!==drag.id)return;
    const point=view.world(event.clientX,event.clientY);if(!point)return;
    change({...drag.pose,x:drag.pose.x+point[0]-drag.start[0],y:drag.pose.y+point[1]-drag.start[1]},100);
  });
  function endDrag(event) {
    if(!drag||event.pointerId!==drag.id)return;
    if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);
    drag=null;canvas.classList.remove('is-dragging');clearTimeout(timer);timer=0;dispatch();
  }
  canvas.addEventListener('pointerup',endDrag);canvas.addEventListener('pointercancel',endDrag);
  canvas.addEventListener('lostpointercapture',()=>{drag=null;canvas.classList.remove('is-dragging');});
  canvas.addEventListener('keydown',event=>{
    if(!pose)return;
    if(event.key==='Home'){event.preventDefault();reset();return;}
    const moves={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,1],ArrowDown:[0,-1]};
    if(!moves[event.key])return;
    event.preventDefault();const [x,y]=moves[event.key],step=event.shiftKey?0.1:0.02;
    change({...pose,x:pose.x+x*step,y:pose.y+y*step});
  });
  new ResizeObserver(()=>{view.resize(config);scheduleDraw();}).observe(canvas);
  async function init() {
    setStatus('Loading the local model and geometry…','loading');
    try {
      const response=await fetch(new URL('./model/config.json',import.meta.url));
      if(!response.ok)throw Error(`Configuration HTTP ${response.status}`);
      config=await response.json();
      if(!config.shapes?.length||!Number.isFinite(config.dx)||!(config.nx>1)||!(config.ny>1))throw Error('Invalid model configuration');
      picker.replaceChildren(...config.shapes.map(shape=>{const option=document.createElement('option');option.value=shape.id;option.textContent=shapeLabels[shape.id]||shape.label;return option;}));
      for(const [key,bounds] of [['x',config.centerX],['y',config.centerY],['size',config.size]]){inputs[key].min=bounds[0];inputs[key].max=bounds[1];}
      for(const control of demo.querySelectorAll('[data-gf-control]'))control.disabled=false;
      const re=config.reynolds??config.Re;
      if(Number.isFinite(re))demo.querySelector('[data-gf-inlet]').textContent=`Fixed low-Re inlet · Re ${re}`;
      startWorker();if(worker)reset();
    } catch(error){console.error('Geometry flow initialization failed:',error);fail('The local model could not be loaded. Refresh the page or retry.');}
  }
  init();
}
