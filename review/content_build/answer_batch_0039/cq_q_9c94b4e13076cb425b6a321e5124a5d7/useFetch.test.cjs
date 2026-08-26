'use strict';
const assert=require('node:assert/strict');
const {createUseFetch}=require('./useFetch.cjs');
function deferred(){let resolve,reject;const promise=new Promise((res,rej)=>{resolve=res;reject=rej;});return {promise,resolve,reject};}
function response(status,data){return {ok:status>=200&&status<=299,status,json:()=>Promise.resolve(data)};}
function createHarness(){
  const states=[],effects=[];let si=0,ei=0;
  const React={
    useState(init){const i=si++;if(!(i in states))states[i]=init;return [states[i],u=>{states[i]=typeof u==='function'?u(states[i]):u;}];},
    useEffect(setup,deps){const i=ei++;const prev=effects[i];const changed=!prev||prev.deps.length!==deps.length||deps.some((d,j)=>!Object.is(d,prev.deps[j]));effects[i]={setup,deps,cleanup:prev?.cleanup,changed};}
  };
  const hook=createUseFetch(React);
  function render(url,fetcher){si=0;ei=0;const result=hook(url,fetcher);for(const e of effects){if(!e.changed)continue;if(e.cleanup)e.cleanup();e.cleanup=e.setup()||undefined;e.changed=false;}return result;}
  function cleanup(){for(const e of effects)if(e.cleanup){e.cleanup();e.cleanup=undefined;}}
  return {states,render,cleanup};
}
async function flush(){await new Promise(resolve=>setImmediate(resolve));await new Promise(resolve=>setImmediate(resolve));}
(async()=>{
  const h=createHarness();const calls=[];const pending=[];
  const fetcher=(url,{signal})=>{const d=deferred();calls.push({url,signal});pending.push(d);return d.promise;};
  h.render('/a',fetcher);assert.equal(calls.length,1);assert.equal(h.states[0].loading,true);
  pending[0].resolve(response(200,{id:'a'}));await flush();assert.deepEqual(h.states[0],{data:{id:'a'},error:null,loading:false});
  h.render('/a',fetcher);assert.equal(calls.length,1);
  h.render('/b',fetcher);assert.equal(calls.length,2);assert.equal(calls[0].signal.aborted,true);
  const old=pending[1];h.render('/c',fetcher);assert.equal(calls.length,3);assert.equal(calls[1].signal.aborted,true);
  old.resolve(response(200,{id:'stale-b'}));await flush();assert.notDeepEqual(h.states[0].data,{id:'stale-b'});
  pending[2].resolve(response(200,{id:'c'}));await flush();assert.deepEqual(h.states[0],{data:{id:'c'},error:null,loading:false});
  h.render('/404',fetcher);pending[3].resolve(response(404,{message:'missing'}));await flush();assert.equal(h.states[0].loading,false);assert.match(h.states[0].error.message,/HTTP 404/);assert.equal(h.states[0].data,null);
  h.render('/network',fetcher);pending[4].reject(new TypeError('network down'));await flush();assert.equal(h.states[0].loading,false);assert.match(h.states[0].error.message,/network down/);
  h.render('/unmount',fetcher);h.cleanup();assert.equal(calls[5].signal.aborted,true);
  console.log('PASS mount-loading success same-url=no-refetch url-change=refetch cleanup=abort stale-write=blocked http-error=recorded network-error=recorded unmount=abort');
})().catch(e=>{console.error(e);process.exit(1);});
