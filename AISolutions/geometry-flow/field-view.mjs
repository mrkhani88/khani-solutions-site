const clamp=(value,low,high)=>Math.max(low,Math.min(high,value));

// Reusable bilinear sampler: physical y grows with grid row index.
function makeSampler(field,config) {
  const {nx,ny,dx,xmin,ymin}=config,inv=1/dx,{u,v,mask}=field;
  return (x,y,out)=>{
    const gx=(x-xmin)*inv-.5,gy=(y-ymin)*inv-.5,i=Math.floor(gx),j=Math.floor(gy);
    if(i<0||j<0||i>=nx-1||j>=ny-1)return false;
    const k=j*nx+i,k1=k+1,k2=k+nx,k3=k2+1;
    if(mask[k]||mask[k1]||mask[k2]||mask[k3])return false;
    const a=gx-i,b=gy-j,wa=(1-a)*(1-b),wb=a*(1-b),wc=(1-a)*b,wd=a*b;
    const qx=wa*u[k]+wb*u[k1]+wc*u[k2]+wd*u[k3],qy=wa*v[k]+wb*v[k1]+wc*v[k2]+wd*v[k3];
    if(!Number.isFinite(qx)||!Number.isFinite(qy))return false;
    out[0]=qx;out[1]=qy;return true;
  };
}
export function sampleVelocity(field,config,x,y) {
  const out=[0,0];return makeSampler(field,config)(x,y,out)?out:null;
}
function traceContext(field,config) {
  return {sample:makeSampler(field,config),stamp:new Uint32Array(config.nx*config.ny),visits:new Uint8Array(config.nx*config.ny),generation:0};
}
function traceSegment(context,config,seedX,seedY,direction=1) {
  const {sample,stamp,visits}=context,generation=++context.generation;
  const q=new Float64Array(2),mid=new Float64Array(2),check=new Float64Array(2);
  const xy=[seedX,seedY],times=[0],h=config.dx,maxStep=.42*h;
  let x=seedX,y=seedY,elapsed=0,distance=0,closed=false,seedU=0,seedV=0,seedSpeed=0;
  for(let n=0;n<config.nx*7;n++) {
    if(!sample(x,y,q))break;
    const speed=Math.hypot(q[0],q[1]);if(speed<.006)break;
    if(n===0){seedU=q[0];seedV=q[1];seedSpeed=speed;}
    let dt=direction*maxStep/speed;
    if(!sample(x+q[0]*dt/2,y+q[1]*dt/2,mid))break;
    dt=direction*maxStep/Math.max(speed,Math.hypot(mid[0],mid[1]));
    if(!sample(x+q[0]*dt/2,y+q[1]*dt/2,mid))break;
    const factor=Math.min(1,.45*h/Math.max(Math.abs(dt)*Math.hypot(mid[0],mid[1]),1e-12));
    const nextX=x+mid[0]*dt*factor,nextY=y+mid[1]*dt*factor;
    if(!sample(nextX,nextY,check))break;
    distance+=Math.hypot(nextX-x,nextY-y);elapsed+=Math.abs(dt)*factor;
    x=nextX;y=nextY;xy.push(x,y);times.push(elapsed);
    // Terminate a genuinely integrated closed orbit without inventing an arc.
    const directionMatch=(check[0]*seedU+check[1]*seedV)/Math.max(seedSpeed*Math.hypot(check[0],check[1]),1e-12);
    if(n>24&&distance>12*h&&Math.hypot(x-seedX,y-seedY)<.2*h&&directionMatch>.95){closed=true;break;}
    const cell=Math.floor((y-config.ymin)/h)*config.nx+Math.floor((x-config.xmin)/h);
    if(stamp[cell]!==generation){stamp[cell]=generation;visits[cell]=1;}
    else if(++visits[cell]>7)break;
  }
  return {xy,times,duration:elapsed,closed};
}
export function traceSteadyStreamline(field,config,seed,direction=1) {
  const segment=traceSegment(traceContext(field,config),config,seed[0],seed[1],direction),points=[];
  for(let i=0;i<segment.xy.length;i+=2)points.push([segment.xy[i],segment.xy[i+1]]);
  return points;
}

// Fixed domain seeds, independent of the selected solid. Occupancy removes
// redundant exterior lines; all paths, including closed ones, follow u/v.
export function buildSteadyPaths(field,config) {
  const context=traceContext(field,config),paths=[],sample=context.sample,probe=new Float64Array(2);
  const sx=config.xmax-config.xmin,sy=config.ymax-config.ymin;
  const coverNx=96,coverNy=48,covered=new Uint8Array(coverNx*coverNy);
  function coverIndex(x,y){
    const i=clamp(Math.floor((x-config.xmin)/sx*coverNx),0,coverNx-1);
    const j=clamp(Math.floor((y-config.ymin)/sy*coverNy),0,coverNy-1);return j*coverNx+i;
  }
  function append(forward,backward,seedIndex) {
    if(forward.xy.length<10)return;
    const xy=[],times=[];
    if(backward&&!forward.closed) {
      for(let i=backward.times.length-1;i>=0;i--){xy.push(backward.xy[2*i],backward.xy[2*i+1]);times.push(backward.duration-backward.times[i]);}
      for(let i=1;i<forward.times.length;i++){xy.push(forward.xy[2*i],forward.xy[2*i+1]);times.push(backward.duration+forward.times[i]);}
    } else {xy.push(...forward.xy);times.push(...forward.times);}
    const duration=times.at(-1);if(!(duration>.02))return;
    for(let i=0;i<xy.length;i+=2)covered[coverIndex(xy[i],xy[i+1])]=1;
    let hash=Math.imul(seedIndex+1,0x45d9f3b);hash^=hash>>>16;hash=Math.imul(hash,0x45d9f3b);hash^=hash>>>16;
    paths.push({xy:new Float64Array(xy),times:new Float64Array(times),duration,closed:forward.closed,phase:(hash>>>0)/4294967296,markers:clamp(Math.ceil(duration/1.65),2,8)});
  }
  const inset=Math.max(.75*config.dx,.0075*sx);
  for(let i=0;i<54;i++) {
    const x=config.xmin+inset,y=config.ymin+inset+(sy-2*inset)*i/53;
    if(sample(x,y,probe))append(traceSegment(context,config,x,y),null,i);
  }
  let seedIndex=54;
  for(let ix=0;ix<15;ix++)for(let iy=0;iy<13;iy++,seedIndex++) {
    const x=config.xmin+sx*(.04375+.9125*ix/14),y=config.ymin+sy*(.05+.90*iy/12);
    if(covered[coverIndex(x,y)]||!sample(x,y,probe))continue;
    const forward=traceSegment(context,config,x,y);
    append(forward,forward.closed?null:traceSegment(context,config,x,y,-1),seedIndex);
  }
  return paths;
}
export function pointAtTravelTime(path,time,out=[0,0]) {
  const target=((time%path.duration)+path.duration)%path.duration,times=path.times;
  let left=0,right=times.length-1;
  while(right-left>1){const mid=(left+right)>>1;if(times[mid]<=target)left=mid;else right=mid;}
  const f=(target-times[left])/Math.max(times[right]-times[left],1e-12);
  out[0]=path.xy[left*2]+f*(path.xy[right*2]-path.xy[left*2]);
  out[1]=path.xy[left*2+1]+f*(path.xy[right*2+1]-path.xy[left*2+1]);return out;
}
const palettes={velocity:[[21,44,105],[24,112,153],[37,185,174],[239,220,104],[223,91,49]],pressure:[[32,74,143],[90,154,199],[237,243,245],[230,159,112],[172,55,53]]};

export function createFieldView(canvas) {
  const ctx=canvas.getContext('2d'),raster=document.createElement('canvas'),rasterCtx=raster.getContext('2d');
  let config=null,field=null,paths=null,screenPath=null,ranges=null,width=1,height=1,dpr=1,transform=null;
  let acceptedPaths=null,acceptedVersion='',version=0,viewVersion=0,motionStart=null;
  let previewKey='',previewPaths=[],rasterMode=null;
  const backgrounds=new Map(),markerPoint=new Float64Array(2),trailPoint=new Float64Array(2);
  function resize(nextConfig) {
    config=nextConfig||config;if(!config)return;
    const rect=canvas.getBoundingClientRect(),nextDpr=Math.min(globalThis.devicePixelRatio||1,2);
    const nextWidth=Math.max(1,rect.width),nextHeight=Math.max(1,rect.height);
    if(transform&&nextWidth===width&&nextHeight===height&&nextDpr===dpr)return;
    width=nextWidth;height=nextHeight;dpr=nextDpr;
    canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);
    const spanX=config.xmax-config.xmin,spanY=config.ymax-config.ymin;
    const scale=Math.max(.001,Math.min((width-24)/spanX,(height-24)/spanY));
    transform={scale,left:(width-spanX*scale)/2,top:(height-spanY*scale)/2,spanX,spanY};
    viewVersion++;screenPath=null;acceptedPaths=null;acceptedVersion='';previewKey='';backgrounds.clear();
  }
  const screenX=x=>transform.left+(x-config.xmin)*transform.scale;
  const screenY=y=>transform.top+(config.ymax-y)*transform.scale;
  function world(clientX,clientY) {
    if(!transform)return null;const rect=canvas.getBoundingClientRect();
    return [config.xmin+(clientX-rect.left-transform.left)/transform.scale,config.ymax-(clientY-rect.top-transform.top)/transform.scale];
  }
  function setField(next,nextConfig) {
    const previous=config;config=nextConfig;field=next;version++;paths=null;screenPath=null;ranges=null;rasterMode=null;
    acceptedPaths=null;acceptedVersion='';previewKey='';backgrounds.clear();
    if(!transform||previous?.nx!==config.nx||previous?.ny!==config.ny||previous?.dx!==config.dx)resize(config);
  }
  function ensureRanges() {
    if(ranges||!field)return;
    const velocity=[],pressure=[],stride=Math.max(1,Math.ceil(field.u.length/1800));
    for(let i=0;i<field.u.length;i+=stride)if(!field.mask[i]){
      const speed=Math.hypot(field.u[i],field.v[i]),cp=field.cp[i];
      if(Number.isFinite(speed))velocity.push(speed);if(Number.isFinite(cp))pressure.push(cp);
    }
    velocity.sort((a,b)=>a-b);pressure.sort((a,b)=>a-b);
    const percentile=(a,f,fallback)=>a.length?a[Math.floor((a.length-1)*f)]:fallback;
    const top=Math.max(.01,percentile(velocity,.98,1));
    const span=Math.max(.01,Math.abs(percentile(pressure,.02,-1)),Math.abs(percentile(pressure,.98,1)));
    ranges={velocity:[0,top],pressure:[-span,span]};
  }
  function ensurePaths() {
    if(!paths)paths=buildSteadyPaths(field,config);
    if(screenPath)return;
    screenPath=new Path2D();
    for(const path of paths)for(let i=0;i<path.xy.length;i+=2){const x=screenX(path.xy[i]),y=screenY(path.xy[i+1]);if(i)screenPath.lineTo(x,y);else screenPath.moveTo(x,y);}
  }
  function paintRaster(mode) {
    if(rasterMode===mode)return;ensureRanges();
    raster.width=config.nx;raster.height=config.ny;
    const image=rasterCtx.createImageData(config.nx,config.ny),range=ranges[mode],palette=palettes[mode],inv=4/(range[1]-range[0]);
    for(let j=0;j<config.ny;j++)for(let i=0;i<config.nx;i++){
      const k=j*config.nx+i;if(field.mask[k])continue;
      const value=mode==='pressure'?field.cp[k]:Math.hypot(field.u[k],field.v[k]);if(!Number.isFinite(value))continue;
      const t=clamp((value-range[0])*inv,0,4),a=Math.min(3,Math.floor(t)),f=t-a,p=((config.ny-1-j)*config.nx+i)*4;
      image.data[p]=palette[a][0]*(1-f)+palette[a+1][0]*f;image.data[p+1]=palette[a][1]*(1-f)+palette[a+1][1]*f;
      image.data[p+2]=palette[a][2]*(1-f)+palette[a+1][2]*f;image.data[p+3]=255;
    }
    rasterCtx.putImageData(image,0,0);rasterMode=mode;
  }
  function background(mode,useField) {
    const key=useField?mode:'empty';if(backgrounds.has(key))return backgrounds.get(key);
    const layer=document.createElement('canvas');layer.width=canvas.width;layer.height=canvas.height;
    const painter=layer.getContext('2d');painter.setTransform(dpr,0,0,dpr,0,0);painter.fillStyle='#0b2234';painter.fillRect(0,0,width,height);
    const {left,top,spanX,spanY,scale}=transform;
    painter.save();painter.beginPath();painter.rect(left,top,spanX*scale,spanY*scale);painter.clip();
    if(useField&&mode!=='streamlines'){paintRaster(mode);painter.imageSmoothingEnabled=true;painter.drawImage(raster,left,top,spanX*scale,spanY*scale);}
    else {
      painter.strokeStyle='rgba(181,216,229,.10)';painter.lineWidth=1;const spacing=spanX/12;painter.beginPath();
      for(let x=config.xmin;x<=config.xmax;x+=spacing){painter.moveTo(screenX(x),screenY(config.ymin));painter.lineTo(screenX(x),screenY(config.ymax));}
      for(let y=config.ymin;y<=config.ymax;y+=spacing){painter.moveTo(screenX(config.xmin),screenY(y));painter.lineTo(screenX(config.xmax),screenY(y));}painter.stroke();
    }
    if(useField){ensurePaths();painter.strokeStyle=mode==='streamlines'?'rgba(157,216,229,.57)':'rgba(10,32,52,.31)';painter.lineWidth=mode==='streamlines'?1.05:.72;painter.stroke(screenPath);}
    painter.restore();painter.strokeStyle='rgba(207,230,238,.25)';painter.strokeRect(left,top,spanX*scale,spanY*scale);
    painter.fillStyle='#bed5df';painter.font='12px system-ui,sans-serif';painter.fillText('Inlet →',left+9,top+19);
    backgrounds.set(key,layer);return layer;
  }
  function polygonPaths(polygons) {
    return polygons.map(poly=>{const path=new Path2D();for(let i=0;i<poly.length;i++){const x=screenX(poly[i][0]),y=screenY(poly[i][1]);if(i)path.lineTo(x,y);else path.moveTo(x,y);}path.closePath();return path;});
  }
  function hitTest(polygons,point) {
    if(!transform||!point)return false;const [x,y]=point,tolerance=8/transform.scale;
    return polygons.some(poly=>{
      let inside=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){
        const a=poly[j],b=poly[i];if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside;
        const vx=b[0]-a[0],vy=b[1]-a[1],length=vx*vx+vy*vy,t=length?clamp(((x-a[0])*vx+(y-a[1])*vy)/length,0,1):0;
        if(Math.hypot(x-a[0]-t*vx,y-a[1]-t*vy)<=tolerance)return true;
      }return inside;
    });
  }
  function drawMarkers(time,mode) {
    if(motionStart===null)motionStart=time;
    const clock=Math.max(0,time-motionStart)*1.04,radius=mode==='streamlines'?1.65:1.15;
    ctx.strokeStyle=mode==='streamlines'?'rgba(255,241,203,.35)':'rgba(10,31,48,.18)';ctx.lineWidth=mode==='streamlines'?1.2:.8;ctx.beginPath();
    for(const path of paths)for(let marker=0;marker<path.markers;marker++){
      const travel=(clock+(path.phase+marker/path.markers)*path.duration)%path.duration;
      if(travel<.10)continue; // Never join a reset marker across the domain.
      pointAtTravelTime(path,travel,markerPoint);pointAtTravelTime(path,travel-.10,trailPoint);
      ctx.moveTo(screenX(trailPoint[0]),screenY(trailPoint[1]));ctx.lineTo(screenX(markerPoint[0]),screenY(markerPoint[1]));
    }ctx.stroke();
    ctx.fillStyle=mode==='streamlines'?'rgba(255,241,203,.94)':'rgba(10,31,48,.40)';ctx.beginPath();
    for(const path of paths)for(let marker=0;marker<path.markers;marker++){
      pointAtTravelTime(path,clock+(path.phase+marker/path.markers)*path.duration,markerPoint);
      const x=screenX(markerPoint[0]),y=screenY(markerPoint[1]);ctx.moveTo(x+radius,y);ctx.arc(x,y,radius,0,2*Math.PI);
    }ctx.fill();
  }
  function draw({polygons=[],previewPolygons=[],mode='streamlines',showField=false,time=0}={}) {
    if(!config||!transform){ctx.fillStyle='#0b2234';ctx.fillRect(0,0,width,height);return;}
    const useField=Boolean(showField&&field),layer=background(mode,useField);ctx.drawImage(layer,0,0,width,height);
    const {left,top,spanX,spanY,scale}=transform;ctx.save();ctx.beginPath();ctx.rect(left,top,spanX*scale,spanY*scale);ctx.clip();
    if(useField)drawMarkers(Number.isFinite(time)?time:0,mode);
    const key=`${version}:${viewVersion}`;
    if(acceptedVersion!==key||!acceptedPaths){acceptedPaths=polygonPaths(polygons);acceptedVersion=key;}
    ctx.setLineDash([]);ctx.fillStyle='#d9c48d';ctx.strokeStyle='#fff0c7';ctx.lineWidth=1.75;
    for(const path of acceptedPaths){ctx.fill(path);ctx.stroke(path);}
    if(previewPolygons.length){
      const key=JSON.stringify(previewPolygons);if(key!==previewKey){previewKey=key;previewPaths=polygonPaths(previewPolygons);}
      ctx.setLineDash([7,5]);ctx.fillStyle='rgba(255,225,160,.12)';ctx.strokeStyle='#ffdc8d';ctx.lineWidth=2.5;
      for(const path of previewPaths){ctx.fill(path);ctx.stroke(path);}
    }
    ctx.restore();
  }
  return {resize,setField,draw,world,hitTest,getRange:mode=>{ensureRanges();return ranges?.[mode]||null;}};
}
