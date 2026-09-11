import test from 'node:test';
import assert from 'node:assert/strict';
import {runCostExample,drawdownExample,orderExample} from '../src/lib/course.js';
const close=(a,b)=>assert(Math.abs(a-b)<1e-8,`${a} != ${b}`);
test('next-open cost example equals independently calculated round trip',()=>{
 const r=runCostExample(10);
 close(r.final,10000/(102*1.001)*99*.999);
 close(r.final,9686.489980607628);
 close(r.benchmark,10000/(102*1.001)*101*.999);
 assert.equal(r.rows[2].net,10000);
 assert.equal(r.rows[3].cash,0);
 assert.equal(r.rows[6].shares,0);
 close(runCostExample(0).final,runCostExample(0).gross);
 assert(runCostExample(100).final<r.final);
});
test('drawdown uses running peak and recovery uses the lower base',()=>{
 const r=drawdownExample(25,20);close(r.maxDrawdown,-.25);close(r.requiredRecovery,100/3);close(r.wealth.at(-1),108);
 const recovered=drawdownExample(50,100);close(recovered.wealth.at(-1),120);close(recovered.maxDrawdown,-.5);
});
test('fills conserve cash, enforce quantity cap and ignore repeated fill ID',()=>{
 const a={id:'a',quantity:4,price:99.9,fee:.4},b={id:'b',quantity:6,price:100,fee:.6};
 const partial=orderExample([a]);assert.equal(partial.state,'PARTIAL');close(partial.cash,1600);
 const full=orderExample([a,a,b,a]);assert.equal(full.state,'FILLED');assert.equal(full.quantity,10);close(full.cash,999.4);close(full.totalFee,1);assert.equal(full.audit[1].status,'duplicate');assert.equal(full.audit[2].fillQuantity,6);
 assert.throws(()=>orderExample([a,b,{...b,id:'c'}]),/Invalid fill/);
 assert.throws(()=>orderExample([a,{...a,price:101}]),/Conflicting fill ID/);
});
