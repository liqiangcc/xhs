'use strict';
const assert=require('assert');
let now=0,nextId=1,timers=new Map();
Date.now=()=>now;
global.setTimeout=(fn,delay)=>{const id=nextId++;timers.set(id,{at:now+delay,fn});return id;};
global.clearTimeout=(id)=>timers.delete(id);
function advance(ms){const end=now+ms;while(true){let chosen=null;for(const [id,t] of timers){if(t.at<=end&&(!chosen||t.at<chosen.t.at))chosen={id,t};}if(!chosen)break;timers.delete(chosen.id);now=chosen.t.at;chosen.t.fn();}now=end;}
const {throttle}=require('./throttle');
const calls=[]; const obj={name:'ctx',run:throttle(function(v){calls.push([Date.now(),this.name,v]);},100)};
obj.run('A'); assert.deepStrictEqual(calls,[[0,'ctx','A']]);
advance(20);obj.run('B');advance(40);obj.run('C');assert.strictEqual(calls.length,1);advance(40);assert.deepStrictEqual(calls[1],[100,'ctx','C']);
advance(100);obj.run('D');assert.deepStrictEqual(calls[2],[200,'ctx','D']);
advance(20);obj.run('E');obj.run.cancel();advance(200);assert.strictEqual(calls.length,3);
obj.run('F');assert.deepStrictEqual(calls[3],[420,'ctx','F']);
assert.throws(()=>throttle(null,10),TypeError);assert.throws(()=>throttle(()=>{},-1),RangeError);
console.log('PASS leading=immediate trailing=latest one-timer-window=verified context=preserved cancel=drops-pending validation=verified');
