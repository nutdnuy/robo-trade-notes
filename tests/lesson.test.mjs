import test from 'node:test';
import assert from 'node:assert/strict';
import {rollingMean,calculateSignals,makeFixture,signalEvents} from '../src/lib/lesson.js';
test('SMA needs a full trailing window and matches hand calculation',()=>{
 assert.deepEqual(rollingMean([10,20,30,40],3),[null,null,20,30]);
});
test('a target based on close cannot appear before the next open',()=>{
 const r=calculateSignals([3,2,1,2,4,6].map((close,i)=>({day:i+1,close})),2,3);
 assert.equal(r[0].signal,'WARMUP');assert.equal(r[1].signal,'WARMUP');
 assert.equal(r[4].target,1);assert.equal(r[4].nextOpenTarget,0);assert.equal(r[5].nextOpenTarget,1);
 assert.deepEqual(signalEvents(r).map(r=>r.day),[5]);
});
test('appending future prices does not change historical signals',()=>{
 const input=makeFixture();
 const full=calculateSignals(input);
 assert.deepEqual(calculateSignals(input.slice(0,70)),full.slice(0,70));
});
test('equal averages mean CASH and invalid windows fail',()=>{
 const r=calculateSignals(Array.from({length:8},(_,i)=>({day:i+1,close:100})),2,4);
 assert.equal(signalEvents(r).length,0);assert.equal(r.at(-1).signal,'CASH');
 assert.throws(()=>calculateSignals(makeFixture(),20,5));
 assert.throws(()=>rollingMean([1,NaN],2));
});
