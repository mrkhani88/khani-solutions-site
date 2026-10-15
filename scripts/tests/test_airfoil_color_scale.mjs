import test from 'node:test';
import assert from 'node:assert/strict';
import {CHORD,createFlow} from '../../AISolutions/airfoil-flow-model.mjs';
import {normalizedFieldBounds,dimensionalFieldScale,fieldColorPosition} from '../../AISolutions/airfoil-color-scale.mjs';
function neighborhood(flow) {
  const samples=[];
  for(let y=-0.45*CHORD;y<0.45*CHORD;y+=0.07)
    for(let x=-0.7*CHORD;x<0.7*CHORD;x+=0.07) samples.push(flow.sample(x,y));
  return samples;
}
test('automatic ranges follow angle and shape while rejecting isolated ideal-flow outliers',()=>{
  const zero=normalizedFieldBounds(neighborhood(createFlow(0)));
  const loaded=normalizedFieldBounds(neighborhood(createFlow(10,{thickness:12,camber:3})));
  assert.ok(loaded.velocity[1]>zero.velocity[1]);
  assert.ok(loaded.pressure[0]<zero.pressure[0]);
  const base=Array.from({length:1000},(_,i)=>({speed:0.5+i/1000,cp:-1+2*i/1000}));
  const robust=normalizedFieldBounds([...base,null,{speed:1e6,cp:-1e12}]);
  assert.ok(robust.velocity[1]<2 && robust.pressure[0]>-2);
});
test('physical legend scales linearly for speed and quadratically for pressure',()=>{
  const bounds=normalizedFieldBounds(neighborhood(createFlow(5)));
  for(const mode of ['velocity','pressure']) {
    const slow=dimensionalFieldScale(bounds,10,mode),fast=dimensionalFieldScale(bounds,20,mode);
    const factor=mode==='velocity'?2:4;
    assert.equal(fast.min,slow.min*factor);assert.equal(fast.max,slow.max*factor);
    assert.equal(fieldColorPosition(slow.max,slow),fieldColorPosition(fast.max,fast));
  }
});
test('pressure colors preserve sign and keep zero neutral with asymmetric limits',()=>{
  const scale={min:-900,max:100,center:0,noWind:false};
  assert.equal(fieldColorPosition(-900,scale),0);
  assert.equal(fieldColorPosition(0,scale),0.5);
  assert.equal(fieldColorPosition(100,scale),1);
  assert.ok(fieldColorPosition(-1,scale)<0.5 && fieldColorPosition(1,scale)>0.5);
  assert.equal(fieldColorPosition(-1e5,scale),0);assert.equal(fieldColorPosition(1e5,scale),1);
});
test('zero wind is a uniform neutral field with zero-valued limits',()=>{
  const bounds=normalizedFieldBounds(neighborhood(createFlow(5)));
  for(const mode of ['velocity','pressure']) {
    const scale=dimensionalFieldScale(bounds,0,mode);
    assert.ok(scale.min===0 && scale.max===0);
    assert.equal(fieldColorPosition(0,scale),0.5);
  }
});
test('auto ranges span the near-airfoil field across the supported geometry and wind controls',()=>{
  for(const angle of [-15,0,15]) for(const thickness of [6,20]) for(const camber of [-6,6]) {
    const samples=neighborhood(createFlow(angle,{thickness,camber}));
    const bounds=normalizedFieldBounds(samples);
    for(const mode of ['velocity','pressure']) for(const wind of [1,20,60]) {
      const scale=dimensionalFieldScale(bounds,wind,mode);
      assert.ok(Number.isFinite(scale.min) && Number.isFinite(scale.max) && scale.max>scale.min);
      const values=samples.filter(Boolean).map(s=>mode==='velocity'?s.speed*wind:s.cp*0.5*1.225*wind**2);
      const clipped=values.filter(v=>v<scale.min || v>scale.max).length/values.length;
      assert.ok(clipped<0.05,'only robust tails are saturated');
    }
  }
});
