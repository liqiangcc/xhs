'use strict';
const assert = require('assert');

function parseUrlToJson(input) {
  if (typeof input !== 'string' || input.length === 0) {
    throw new TypeError('input must be a non-empty absolute URL string');
  }
  const url = new URL(input);
  const query = Object.create(null);
  for (const [key, value] of url.searchParams) {
    if (!Object.hasOwn(query, key)) query[key] = value;
    else if (Array.isArray(query[key])) query[key].push(value);
    else query[key] = [query[key], value];
  }
  return JSON.stringify({
    protocol: url.protocol.endsWith(':') ? url.protocol.slice(0, -1) : url.protocol,
    hostname: url.hostname || null,
    port: url.port || null,
    pathname: url.pathname,
    query,
    fragment: url.hash ? url.hash.slice(1) : null,
  });
}

function parse(input) { return JSON.parse(parseUrlToJson(input)); }

assert.deepStrictEqual(parse('https://example.com:8443/a/b?tag=java&tag=js&empty=#top'), {
  protocol:'https', hostname:'example.com', port:'8443', pathname:'/a/b', query:{tag:['java','js'],empty:''}, fragment:'top'
});
assert.deepStrictEqual(parse('https://example.com:443/p'), {protocol:'https',hostname:'example.com',port:null,pathname:'/p',query:{},fragment:null});
assert.deepStrictEqual(parse('http://[2001:db8::1]:8080/a?x=1'), {protocol:'http',hostname:'[2001:db8::1]',port:'8080',pathname:'/a',query:{x:'1'},fragment:null});
assert.deepStrictEqual(parse('ftp://example.com/file?q=a+b'), {protocol:'ftp',hostname:'example.com',port:null,pathname:'/file',query:{q:'a b'},fragment:null});
assert.deepStrictEqual(parse('custom:opaque?x=1'), {protocol:'custom',hostname:null,port:null,pathname:'opaque',query:{x:'1'},fragment:null});
assert.deepStrictEqual(parse('https://x.test/a%20b?q=%E4%B8%AD'), {protocol:'https',hostname:'x.test',port:null,pathname:'/a%20b',query:{q:'中'},fragment:null});
assert.deepStrictEqual(parse('https://x.test/?__proto__=x'), {protocol:'https',hostname:'x.test',port:null,pathname:'/',query:{'__proto__':'x'},fragment:null});
assert.throws(() => parseUrlToJson('/relative?x=1'), TypeError);
assert.throws(() => parseUrlToJson(''), TypeError);
assert.throws(() => parseUrlToJson(null), TypeError);

const generated = 5000;
for (let i=0;i<generated;i++) {
  const port=8000+(i%1000);
  const input=`https://h${i}.example:${port}/p${i}%20x?a=x${i}&a=y${i}&empty=#f${i}`;
  assert.deepStrictEqual(parse(input), {
    protocol:'https', hostname:`h${i}.example`, port:String(port), pathname:`/p${i}%20x`, query:{a:[`x${i}`,`y${i}`],empty:''}, fragment:`f${i}`
  });
}
console.log(`PASS deterministic=10 generated=${generated} repeated-query=preserved default-port=normalized ipv6=covered opaque-scheme=covered percent-encoding=covered proto-key=safe relative=rejected`);
