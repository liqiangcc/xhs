'use strict';
const assert=require('assert');
const {EventEmitter}=require('./EventEmitter');
const ee=new EventEmitter();
assert.strictEqual(ee.emit('missing'),false);
const seen=[];
function a(x,y){assert.strictEqual(this,ee);seen.push(`a:${x+y}`)}
function b(x,y){seen.push(`b:${x*y}`)}
ee.on('calc',a).on('calc',b);
assert.strictEqual(ee.emit('calc',2,3),true);
assert.deepStrictEqual(seen,['a:5','b:6']);
let onceCount=0;
function onlyOnce(){onceCount++;ee.emit('reentrant')}
ee.once('reentrant',onlyOnce);ee.emit('reentrant');
assert.strictEqual(onceCount,1);
let cancelled=0;function cancelledOnce(){cancelled++}
ee.once('cancel',cancelledOnce).off('cancel',cancelledOnce);
assert.strictEqual(ee.emit('cancel'),false);assert.strictEqual(cancelled,0);
let duplicate=0;function dup(){duplicate++}
ee.on('dup',dup).on('dup',dup).off('dup',dup);
assert.strictEqual(ee.emit('dup'),false);assert.strictEqual(duplicate,0);
const mutation=[];function late(){mutation.push('late')}
function first(){mutation.push('first');ee.on('mut',late);ee.off('mut',second)}
function second(){mutation.push('second')}
ee.on('mut',first).on('mut',second);ee.emit('mut');
assert.deepStrictEqual(mutation,['first','second']);mutation.length=0;ee.emit('mut');
assert.deepStrictEqual(mutation,['first','late']);
const fail=new EventEmitter();let after=false;
fail.on('x',()=>{throw new Error('boom')}).on('x',()=>{after=true});
assert.throws(()=>fail.emit('x'),/boom/);assert.strictEqual(after,false);
console.log('PASS order-args-this=true once-reentrant=1 off-once=true off-duplicates=all snapshot=true mutation-next-round=true error-propagation=true');
