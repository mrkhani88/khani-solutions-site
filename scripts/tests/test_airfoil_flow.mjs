import test from 'node:test';
import assert from 'node:assert/strict';
import {createFlow, outline, traceStreamline} from '../../AISolutions/airfoil-flow-model.mjs';

test('zero incidence is symmetric and has zero circulation', () => {
  const flow = createFlow(0);
  assert.equal(flow.circulation, 0);
  for (const [x,y] of [[-3,1],[-1,0.6],[1,0.7],[3,1]]) {
    const upper=flow.velocity(x,y), lower=flow.velocity(x,-y);
    assert.ok(Math.abs(upper[0]-lower[0])<1e-10);
    assert.ok(Math.abs(upper[1]+lower[1])<1e-10);
  }
});
test('solid interior has no fluid velocity and distant flow is horizontal', () => {
  for (const angle of [-15,0,15]) {
    const flow=createFlow(angle);
    assert.equal(flow.velocity(0,0),null);
    const v=flow.velocity(-10000,100);
    assert.ok(Math.abs(v[0]-1)<0.001 && Math.abs(v[1])<0.001);
  }
});
test('surface velocity is tangential and the trailing-edge Kutta limit stays finite', () => {
  for (const angle of [-15,0,15]) {
    const flow=createFlow(angle), points=outline(angle,360);
    for(let i=3;i<357;i+=7) {
      const tangent=[points[i+1][0]-points[i-1][0],points[i+1][1]-points[i-1][1]];
      const v=flow.velocity(...points[i]);
      assert.ok(v,'velocity defined on surface');
      const normalSpeed=Math.abs(v[0]*tangent[1]-v[1]*tangent[0])/Math.hypot(...tangent);
      assert.ok(normalSpeed<0.001*Math.max(1,Math.hypot(...v)),'no significant flow through the surface');
    }
    const v=flow.velocity(...points[0]);
    assert.ok(v && Math.hypot(...v)<2,'finite cusp velocity');
  }
});
test('changing incidence changes flow and reverses circulation', () => {
  const positive=createFlow(10), negative=createFlow(-10);
  assert.ok(positive.circulation>0);
  assert.equal(positive.circulation,-negative.circulation);
  assert.ok(Math.abs(positive.velocity(0,0.8)[0]-negative.velocity(0,0.8)[0])>0.1);
});
test('field samples obey Bernoulli, mask the solid, and recover freestream values', () => {
  for (const angle of [-15, 0, 15]) {
    const flow = createFlow(angle);
    assert.equal(flow.sample(0, 0), null);
    for (const [x, y] of [[-3, 1], [0, 0.8], [1, -0.8], [3, 1]]) {
      const sample = flow.sample(x, y);
      assert.ok(sample && Number.isFinite(sample.cp) && sample.speed >= 0);
      assert.ok(Math.abs(sample.cp + sample.speed ** 2 - 1) < 1e-12);
    }
    const far = flow.sample(100000, 100);
    assert.ok(Math.abs(far.speed - 1) < 0.0001 && Math.abs(far.cp) < 0.0001);
  }
  const flow = createFlow(0);
  const nose = outline(0, 360)[180];
  assert.ok(flow.sample(...nose).speed < 1e-10);
  assert.equal(flow.sample(...nose).cp, 1);
  assert.ok(createFlow(10).sample(0, 0.8).cp < createFlow(10).sample(0, -0.8).cp);
});
test('streamlines remain outside the solid and cross the viewing region', () => {
  for (const angle of [-15,0,15]) {
    const flow=createFlow(angle);
    let exits=0;
    for(let i=0;i<30;i++) {
      const line=traceStreamline(flow,-5.7,-2+(i+0.5)*4/30,{xMin:-5.7,xMax:5.7,yMax:2});
      assert.ok(line.points.length>20);
      assert.ok(line.points.every(p=>flow.velocity(p.x,p.y)!==null));
      if(line.points.at(-1).x>5.7) exits++;
    }
    assert.ok(exits>=18,'most inlet streamlines traverse the domain');
  }
});
