const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

export function sampleVelocity(field, config, x, y) {
  const {nx, ny, dx, xmin, ymin} = config;
  const gx = (x - xmin) / dx - 0.5, gy = (y - ymin) / dx - 0.5;
  const i = Math.floor(gx), j = Math.floor(gy);
  if (i < 0 || j < 0 || i >= nx - 1 || j >= ny - 1) return null;
  const ids = [j * nx + i, j * nx + i + 1, (j + 1) * nx + i, (j + 1) * nx + i + 1];
  if (ids.some(k => field.mask[k])) return null;
  const a = gx - i, b = gy - j;
  const weights = [(1-a)*(1-b), a*(1-b), (1-a)*b, a*b];
  const u = ids.reduce((s,k,n) => s + weights[n] * field.u[k], 0);
  const v = ids.reduce((s,k,n) => s + weights[n] * field.v[k], 0);
  return Number.isFinite(u) && Number.isFinite(v) ? [u,v] : null;
}

export function traceSteadyStreamline(field, config, seed, direction = 1) {
  let [x,y] = seed;
  const points = [[x,y]], visited = new Map();
  for (let n = 0; n < config.nx * 9; n++) {
    const q = sampleVelocity(field, config, x, y);
    if (!q) break;
    const speed = Math.hypot(...q);
    if (speed < 0.008) break;
    let dt = direction * 0.42 * config.dx / speed;
    let mid = sampleVelocity(field, config, x + q[0]*dt/2, y + q[1]*dt/2);
    if (!mid) break;
    dt = direction * 0.42 * config.dx / Math.max(speed,Math.hypot(...mid));
    mid = sampleVelocity(field, config, x + q[0]*dt/2, y + q[1]*dt/2);
    if (!mid) break;
    const stepScale = Math.min(1,0.45*config.dx/Math.max(Math.abs(dt)*Math.hypot(...mid),1e-12));
    const next = [x + mid[0]*dt*stepScale, y + mid[1]*dt*stepScale];
    if (!sampleVelocity(field, config, ...next)) break;
    [x,y] = next; points.push(next);
    const cell = Math.floor((y-config.ymin)/config.dx)*config.nx + Math.floor((x-config.xmin)/config.dx);
    const count = (visited.get(cell) || 0) + 1;
    visited.set(cell, count);
    if (count > 8) break;
  }
  return points;
}

function limits(values, mask, symmetric = false) {
  const finite = [];
  for (let i=0;i<values.length;i++) if (!mask[i] && Number.isFinite(values[i])) finite.push(values[i]);
  finite.sort((a,b)=>a-b);
  if (!finite.length) return symmetric ? [-1,1] : [0,1];
  let lo=finite[Math.floor((finite.length-1)*0.02)], hi=finite[Math.floor((finite.length-1)*0.98)];
  if (symmetric) { const m=Math.max(Math.abs(lo),Math.abs(hi),0.01); return [-m,m]; }
  lo=Math.min(0,lo); return [lo,Math.max(hi,lo+0.01)];
}

const palettes = {
  velocity: [[21,44,105],[24,112,153],[37,185,174],[239,220,104],[223,91,49]],
  pressure: [[32,74,143],[90,154,199],[237,243,245],[230,159,112],[172,55,53]],
};
function color(value, range, palette) {
  const t=clamp((value-range[0])/(range[1]-range[0]),0,1)*(palette.length-1);
  const a=Math.min(palette.length-2,Math.floor(t)), f=t-a;
  return palette[a].map((v,i)=>Math.round(v*(1-f)+palette[a+1][i]*f));
}

export function createFieldView(canvas) {
  const ctx=canvas.getContext('2d'), raster=document.createElement('canvas'), rasterCtx=raster.getContext('2d');
  let config=null, field=null, lines=[], speed=null, ranges=null, width=1, height=1, transform=null, rasterMode=null;
  function resize(nextConfig) {
    config=nextConfig || config;
    if (!config) return;
    const rect=canvas.getBoundingClientRect(), dpr=Math.min(devicePixelRatio || 1,2);
    width=Math.max(1,rect.width); height=Math.max(1,rect.height);
    canvas.width=Math.round(width*dpr); canvas.height=Math.round(height*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    const spanX=config.xmax-config.xmin,spanY=config.ymax-config.ymin;
    const scale=Math.min((width-24)/spanX,(height-24)/spanY);
    transform={scale,left:(width-spanX*scale)/2,top:(height-spanY*scale)/2,spanX,spanY};
  }
  function screen([x,y]) { return [transform.left+(x-config.xmin)*transform.scale,transform.top+(config.ymax-y)*transform.scale]; }
  function world(clientX,clientY) {
    if (!transform) return null;
    const rect=canvas.getBoundingClientRect();
    return [config.xmin+(clientX-rect.left-transform.left)/transform.scale,config.ymax-(clientY-rect.top-transform.top)/transform.scale];
  }
  function setField(next, nextConfig) {
    config=nextConfig;field=next;
    speed=Float32Array.from(next.u,(u,i)=>Math.hypot(u,next.v[i]));
    ranges={velocity:limits(speed,next.mask),pressure:limits(next.cp,next.mask,true)};
    rasterMode=null;lines=[];
    const inset=2.1*config.dx, spanY=config.ymax-config.ymin;
    for(let i=0;i<25;i++) {
      const seed=[config.xmin+inset,config.ymin+inset+(spanY-2*inset)*(i+0.5)/25];
      const line=traceSteadyStreamline(field,config,seed);
      if(line.length>4) lines.push(line);
    }
    // Additional seeds inspect the predicted wake; their paths still come only from u/v.
    for(const fraction of [0.47,0.68]) for(let i=1;i<8;i++) {
      const seed=[config.xmin+fraction*(config.xmax-config.xmin),config.ymin+i*spanY/8];
      if(!sampleVelocity(field,config,...seed)) continue;
      const backward=traceSteadyStreamline(field,config,seed,-1).reverse();
      const forward=traceSteadyStreamline(field,config,seed,1);
      const line=backward.concat(forward.slice(1));
      if(line.length>12)lines.push(line);
    }
    resize(config);
  }
  function paintRaster(mode) {
    if(rasterMode===mode)return;
    raster.width=config.nx;raster.height=config.ny;
    const image=rasterCtx.createImageData(config.nx,config.ny),values=mode==='pressure'?field.cp:speed;
    for(let j=0;j<config.ny;j++)for(let i=0;i<config.nx;i++) {
      const k=j*config.nx+i,p=((config.ny-1-j)*config.nx+i)*4;
      if(field.mask[k] || !Number.isFinite(values[k]))continue;
      const c=color(values[k],ranges[mode],palettes[mode]);
      image.data[p]=c[0];image.data[p+1]=c[1];image.data[p+2]=c[2];image.data[p+3]=255;
    }
    rasterCtx.putImageData(image,0,0);rasterMode=mode;
  }
  function polygonPaths(polygons) {
    return polygons.map(poly=>{
      const p=new Path2D();poly.forEach((point,i)=>{const [x,y]=screen(point);if(i)p.lineTo(x,y);else p.moveTo(x,y);});p.closePath();return p;
    });
  }
  function hitTest(polygons,point) {
    if(!transform || !point)return false;
    const [x,y]=point,tolerance=8/transform.scale;
    return polygons.some(poly=>{
      let inside=false;
      for(let i=0,j=poly.length-1;i<poly.length;j=i++) {
        const a=poly[j],b=poly[i];
        if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside;
        const vx=b[0]-a[0],vy=b[1]-a[1],length=vx*vx+vy*vy;
        const t=length?clamp(((x-a[0])*vx+(y-a[1])*vy)/length,0,1):0;
        if(Math.hypot(x-a[0]-t*vx,y-a[1]-t*vy)<=tolerance)return true;
      }
      return inside;
    });
  }
  function draw({polygons=[],mode='streamlines',preview=false,showField=false}={}) {
    ctx.clearRect(0,0,width,height);ctx.fillStyle='#0b2234';ctx.fillRect(0,0,width,height);
    if(!config || !transform)return;
    const box=[transform.left,transform.top,transform.spanX*transform.scale,transform.spanY*transform.scale];
    ctx.save();ctx.beginPath();ctx.rect(...box);ctx.clip();
    if(showField && field && mode!=='streamlines') {paintRaster(mode);ctx.imageSmoothingEnabled=true;ctx.drawImage(raster,...box);}
    else {
      ctx.strokeStyle='rgba(181,216,229,.10)';ctx.lineWidth=1;
      const spacing=(config.xmax-config.xmin)/12;
      for(let x=config.xmin;x<=config.xmax;x+=spacing){const a=screen([x,config.ymin]),b=screen([x,config.ymax]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();}
      for(let y=config.ymin;y<=config.ymax;y+=spacing){const a=screen([config.xmin,y]),b=screen([config.xmax,y]);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();}
    }
    if(showField && field) {
      ctx.strokeStyle=mode==='streamlines'?'rgba(166,220,231,.79)':'rgba(10,32,52,.49)';ctx.lineWidth=mode==='streamlines'?1.25:0.85;
      for(const line of lines){ctx.beginPath();line.forEach((p,i)=>{const s=screen(p);if(i)ctx.lineTo(...s);else ctx.moveTo(...s);});ctx.stroke();}
    }
    ctx.setLineDash(preview?[7,5]:[]);ctx.fillStyle=preview?'rgba(226,192,121,.23)':'#d9c48d';ctx.strokeStyle=preview?'#ffdb89':'#fff0c7';ctx.lineWidth=preview?2.5:1.75;
    for(const path of polygonPaths(polygons)){ctx.fill(path);ctx.stroke(path);}
    ctx.restore();ctx.strokeStyle='rgba(207,230,238,.25)';ctx.lineWidth=1;ctx.strokeRect(...box);
    ctx.fillStyle='#bed5df';ctx.font='12px system-ui,sans-serif';ctx.fillText('Inlet →',transform.left+9,transform.top+19);
  }
  return {resize,setField,draw,world,hitTest,getRange:mode=>ranges?.[mode] || null};
}
