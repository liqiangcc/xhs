'use strict';
function throttle(fn, wait) {
  if (typeof fn !== 'function') throw new TypeError('fn must be a function');
  if (!Number.isFinite(wait) || wait < 0) throw new RangeError('wait must be non-negative');
  let lastInvokeTime=-Infinity,timerId=null,pendingThis,pendingArgs;
  function invoke(time,receiver,args){lastInvokeTime=time;pendingThis=pendingArgs=undefined;return fn.apply(receiver,args);}
  function trailing(){timerId=null;if(pendingArgs!==undefined)invoke(Date.now(),pendingThis,pendingArgs);}
  function throttled(...args){const now=Date.now();const remaining=wait-(now-lastInvokeTime);if(remaining<=0){if(timerId!==null){clearTimeout(timerId);timerId=null;}return invoke(now,this,args);}pendingThis=this;pendingArgs=args;if(timerId===null)timerId=setTimeout(trailing,remaining);}
  throttled.cancel=function(){if(timerId!==null)clearTimeout(timerId);timerId=null;pendingThis=pendingArgs=undefined;lastInvokeTime=-Infinity;};
  return throttled;
}
module.exports={throttle};
