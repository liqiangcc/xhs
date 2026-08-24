<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_5e21e188af5c4a9ffdb5eaf97cc39c97","version":1,"status":"draft","updated_at":"2026-08-25","answer_type":"coding","quality_tier":"candidate"} -->
# 如何实现一个深拷贝函数？

## 核心结论

“深拷贝”必须先定义支持范围，不能把一个递归函数说成能复制所有 JavaScript 对象。这里给出一个可执行契约：复制 primitive、Array、普通对象和 `Object.create(null)` 对象；递归复制数据属性，用 `WeakMap` 保持循环引用与共享引用拓扑；保留 symbol/non-enumerable/accessor descriptor；Date、Map、Set、DOM 节点和自定义 class 实例不在本实现范围内，遇到非普通对象直接报错。

## 1 分钟版

- primitive（包括函数引用）直接返回；真正需要递归的是非 `null` object。
- Array 新建同长度数组；普通对象按原 prototype 新建空壳。
- 在递归子属性之前先把 `source -> clone` 放进 `WeakMap`，这样环形引用不会无限递归，同一个源对象被多处引用时也会映射到同一个克隆对象。
- 用 `Reflect.ownKeys` + property descriptor 复制 symbol、不可枚举属性和 getter/setter；descriptor 中的数据值才递归深拷贝。
- 对 Date/Map/Set/TypedArray/DOM/自定义 class 等对象必须逐类定义语义；本题来源没有给范围，所以这里选择显式拒绝，而不是悄悄复制错。

## 3 分钟版

```javascript
function deepClone(value, seen = new WeakMap()) {
  if (value === null || typeof value !== 'object') return value;
  if (seen.has(value)) return seen.get(value);

  const isArray = Array.isArray(value);
  const proto = Object.getPrototypeOf(value);
  if (!isArray && proto !== Object.prototype && proto !== null) {
    throw new TypeError('unsupported object type');
  }

  const copy = isArray ? new Array(value.length) : Object.create(proto);
  seen.set(value, copy);

  for (const key of Reflect.ownKeys(value)) {
    if (isArray && key === 'length') continue;
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if ('value' in descriptor) {
      descriptor.value = deepClone(descriptor.value, seen);
    }
    Object.defineProperty(copy, key, descriptor);
  }
  return copy;
}
```

这个版本的关键不是“递归”两个字，而是先定义对象域，再保证对象图关系正确。若 `a.left === a.right`，克隆后也应保持 `b.left === b.right`，但 `b.left !== a.left`；若 `a.self === a`，克隆后应有 `b.self === b`。

## 关键细节

- `typeof null === "object"`，必须先单独处理 `null`。
- `WeakMap` 要在遍历子属性前写入，否则自环在第一次递归时仍然找不到已创建副本。
- `Reflect.ownKeys` 同时包含字符串键和 symbol 键；descriptor 能保留 enumerable/writable/configurable 以及 getter/setter，而不会为了读取 accessor 主动触发 getter。
- 数组先以原 `length` 创建，跳过不可配置的 `length` descriptor，再复制实际 own keys，可保留稀疏数组的洞。
- 函数不是普通可复制状态对象，本契约把函数当作不可变行为引用按 identity 保留；如果要求复制闭包，本质上已超出普通对象深拷贝能定义的范围。
- 复杂度按可达对象图计：时间 O(P)，P 是访问到的 own property 总数；额外空间 O(N + D)，N 是记录进 `WeakMap` 的对象数，D 是递归深度。极深链可能造成调用栈溢出，可改成显式栈遍历。

## 原理机制

深拷贝本质上是“复制对象图”，不是“把 JSON 重新 parse 一遍”。节点是对象，属性引用是边。`WeakMap` 记录旧节点到新节点的一一映射：第一次遇到节点时先创建新节点并登记，再递归复制出边；后续再次遇到同一旧节点直接复用映射，因此既终止环，也保留 alias。JSON round-trip 会丢失 `undefined`、symbol、descriptor、循环结构等信息，所以只能用于一个更窄的 JSON 数据域。

## 项目经验版

来源没有提供真实项目经历，不能虚构“线上用过某个深拷贝库”。实际落地时应先问清数据域：如果只需要平台支持的结构化可克隆类型，优先评估 `structuredClone`；如果业务有 class/Map/Date 等自定义语义，就按类型建立明确 clone policy 和测试，而不是无限扩张一个通用递归函数。

## 常见追问

- 问：为什么要用 `WeakMap`，普通 `Map` 不行吗？答：两者都能解决本次遍历的环和共享引用；`WeakMap` 不会因为这个辅助映射额外强持有对象，更贴合临时对象映射用途。
- 问：为什么 `JSON.parse(JSON.stringify(x))` 不算通用深拷贝？答：它只适合 JSON 可表达的数据域，循环引用会失败，symbol/undefined/descriptor 等语义也不会被保留。
- 问：Date、Map、Set 怎么办？答：必须为每种类型定义复制规则，例如 key/value 是否递归、prototype 是否保留；本实现显式拒绝，避免得到“长得像但语义错”的普通对象。
- 问：循环引用为什么不会递归爆掉？答：源对象第一次出现时，在递归属性前就写入 `seen`；再次遇到它直接返回已创建副本。
- 问：递归会有什么边界？答：对象图极深时可能超过调用栈，需要改为显式 worklist；这不改变 `seen` 映射的不变量。

## 易错点

- 把 `null` 当普通对象递归。
- 先递归子属性再写 `WeakMap`，导致循环引用无限递归。
- 只用 `Object.keys` 却宣称完整保留 symbol/non-enumerable 属性。
- 对 Date/Map/Set/class 实例直接 `Object.create(proto)`，表面 prototype 相同但内部槽没有复制，得到不可用对象。
- 把函数闭包、DOM 节点等未定义语义的对象也称作“通用深拷贝”。
