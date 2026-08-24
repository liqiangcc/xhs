<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_2fcd783bcefb0f3ab525b18afe3a7591","version":1,"status":"draft","updated_at":"2026-08-24","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：手写 Promise.all 的实现

## 核心结论

仓库来源明确保留了“手写 Promise.all 的实现”，并给出一个按数组 `length` 遍历的参考实现。这里做一个**显式的规范完整性扩展**：候选实现接受任意同步 iterable，而不只数组；这不是从题干恢复出的额外要求，而是为了贴近 ECMAScript `Promise.all(iterable)` 的公开语义。

实现要守住四个核心性质：每个输入都通过 `Promise.resolve` 做值/thenable 吸收；输出数组按**输入迭代顺序**排列而不是按完成顺序；空 iterable 兑现为 `[]`；任一输入拒绝时，聚合 Promise 以最先观察到的拒绝原因进入 rejected。拒绝聚合结果不会取消其他已经启动的异步任务。

本候选是一个独立函数 `myPromiseAll(iterable)`，内部固定使用原生 `Promise`。它不声称完整复刻规范中“以 `this` 作为构造器、支持 Promise 子类构造器泛化”的静态方法细节；面试手写层面重点验证聚合语义、顺序、空输入、thenable 吸收与拒绝路径。

## 1 分钟版

我会这样写：遍历输入时给每个元素分配固定下标，并立即用 `Promise.resolve(value)` 包装。某个元素完成时，把结果写回它自己的下标，所以即使第 3 个先完成，最终数组顺序仍然和输入一致。

用一个 `remaining` 计数器表示还有多少元素没完成。这里从 `1` 开始，遍历每个元素时 `+1`，遍历结束后再 `-1`；这样空 iterable 会直接得到 `0` 并 `resolve([])`，非空输入则要等所有 fulfillment 回调都把计数减到 `0` 才 resolve。任何一个 Promise reject 时直接调用外层 `reject`。

核心代码：

```js
function myPromiseAll(iterable) {
  return new Promise((resolve, reject) => {
    const results = [];
    let remaining = 1;
    let index = 0;

    for (const value of iterable) {
      const currentIndex = index++;
      results.push(undefined);
      remaining++;

      Promise.resolve(value).then(
        (resolvedValue) => {
          results[currentIndex] = resolvedValue;
          if (--remaining === 0) resolve(results);
        },
        reject,
      );
    }

    if (--remaining === 0) resolve(results);
  });
}
```

## 3 分钟版

仓库图片里的参考实现是数组版：用 `for (let i = 0; i < promises.length; i++)` 遍历，`Promise.resolve` 包装每个输入，用 `results[i]` 保序，全部完成后 resolve，任一失败直接 reject，并单独处理空数组。这个方向是对的。

候选实现把“数组遍历”扩展成 `for...of`，因此支持数组、`Set`、generator 等同步 iterable。扩展之后仍然保持相同的聚合不变量：第 `i` 次迭代产生的输入只能写 `results[i]`，完成顺序不能改变槽位归属；`remaining` 只在注册一个输入时增加一次，只在该输入成功兑现时减少一次。

为什么先 `Promise.resolve(value)`？因为输入不一定已经是 Promise：可以是普通值，也可以是 thenable。原生 `Promise.resolve` 会把它统一成可按 Promise 语义观察的对象。这样 `[1, Promise.resolve(2), thenable]` 可以放在同一个聚合里。

为什么不能 `results.push(resolvedValue)`？因为 Promise 完成顺序通常不同于输入顺序。如果第二个任务先完成，直接 push 会把它错误地放到结果第一个位置。必须在遍历时冻结 `currentIndex`，完成后按这个位置赋值。

为什么 `remaining` 从 `1` 开始？它相当于给“输入迭代尚未结束”留一个哨兵。遍历完统一减掉这一个；若没有任何元素，马上变成 `0`，因此空 iterable 得到 `[]`。非空时，每个输入又各自占一个计数，直到全部成功才归零。对本实现而言，`Promise.resolve(...).then(...)` 回调本来就是异步执行的，简单计数也能工作；使用哨兵能让控制结构更接近规范里的 `PerformPromiseAll` 思路，并把空输入自然统一进去。

拒绝路径上，任一输入 reject 就调用外层 `reject`。外层 Promise 一旦 settled，后续 resolve/reject 调用不会改变状态。但这不等于“取消其他任务”：已经创建或启动的 Promise 仍会继续执行，只是聚合 Promise 不再等待它们决定最终结果。

复杂度方面，遍历和结果写入是 `O(n)`，结果数组及每个元素的闭包/处理器带来 `O(n)` 附加状态。`Promise.all` 是聚合器，不是并发限流器；它不会把任务串行化，也没有内建并发上限。

## 关键细节

- **题源边界**：仓库题源支持“手写 Promise.all”，图片还保留了数组版参考实现；“接受任意 iterable”是本候选为了贴近 ECMAScript 规范做的明确扩展。
- **值吸收**：每个输入先走 `Promise.resolve`，因此普通值、Promise 和 thenable 可以统一处理。
- **结果顺序**：结果按输入迭代顺序保存，不按实际完成顺序保存。
- **空输入**：空 iterable 最终兑现为 `[]`；`then` 回调仍然按 Promise 微任务语义异步执行。
- **拒绝路径**：最先被聚合逻辑观察到的 rejection 会决定外层 Promise 的拒绝原因；其他任务不会因此自动取消。
- **iterable 异常**：如果读取 iterator 或迭代过程中同步抛错，异常发生在 Promise executor 内，会把返回的聚合 Promise 置为 rejected。
- **实现边界**：本函数固定使用原生 `Promise` / `Promise.resolve`；没有复刻规范静态方法基于 `this` 构造器的泛化行为。
- **复杂度**：聚合维护 `O(n)` 结果和处理器状态；它没有把异步任务变成串行执行，也不提供限流。
- **可验证性**：固定用例覆盖空数组、普通值、乱序完成、嵌套 Promise、thenable、拒绝、`Set`、generator、稀疏数组和 iterator 抛错；另有 2000 组确定性随机输入，与原生 `Promise.all` 对照。

## 原理机制

```js
'use strict';

function myPromiseAll(iterable) {
  return new Promise((resolve, reject) => {
    const results = [];
    let remaining = 1;
    let index = 0;

    for (const value of iterable) {
      const currentIndex = index++;
      results.push(undefined);
      remaining++;

      Promise.resolve(value).then(
        (resolvedValue) => {
          results[currentIndex] = resolvedValue;
          remaining--;
          if (remaining === 0) {
            resolve(results);
          }
        },
        reject,
      );
    }

    remaining--;
    if (remaining === 0) {
      resolve(results);
    }
  });
}
```

候选实现的精确验证输出为：

```text
PASS fixed=12 randomized=2000 oracle=native-Promise.all iterable=supported order=input reject=first-observed thenable=adopted empty=fulfilled
```

随机验证生成普通值、异步 fulfillment、异步 rejection 和 thenable 的混合输入；对同一描述分别构造新输入，比较原生 `Promise.all` 与候选实现的 fulfilled/rejected 结果。固定用例额外覆盖非数组 iterable、稀疏数组、iterator 抛错以及空输入的异步回调行为。

## 项目经验版

这是前端基础手撕题，仓库来源没有真实生产项目上下文，因此不编造线上经历。工程中如果只是“等待一组已经确定的异步任务全部完成”，优先直接使用原生 `Promise.all`。如果任务数量很大、需要并发上限、超时、取消、重试或部分成功策略，应在更上层增加调度器或改用适合的组合方式，而不是修改 `Promise.all` 的基本聚合语义。

## 常见追问

- 问：为什么结果不能在完成时直接 `push`？答：因为完成顺序不等于输入顺序；必须先保存输入下标，再把 fulfillment value 写回固定槽位。
- 问：为什么要 `Promise.resolve(value)`？答：为了统一普通值、原生 Promise 和 thenable 的处理；否则直接调用 `value.then` 会在普通值上失败，也可能漏掉 thenable 吸收语义。
- 问：空数组怎么处理？答：遍历不到任何元素，哨兵计数从 `1` 减到 `0`，立即 `resolve([])`；对调用者来说，后续 `.then(...)` 仍通过微任务执行。
- 问：某个 Promise reject 后，其他请求会被取消吗？答：不会。聚合 Promise 会进入 rejected，但已经启动的异步操作仍继续，除非这些操作自身支持并由上层显式触发取消。
- 问：为什么这里支持 `Set` 和 generator？答：这是候选为了贴近 `Promise.all(iterable)` 做的规范完整性扩展；仓库图片中的参考实现本身只按数组 `length` 遍历。
- 问：这是不是 100% 等价于原生静态 `Promise.all`？答：不是。本候选覆盖主要聚合行为，但固定使用原生 `Promise`，没有实现规范里基于静态方法 `this` 构造器的泛型构造能力；面试手写时应明确这个边界。
- 问：`Promise.all` 能控制并发数吗？答：不能。它只聚合传入的值/Promise；任务通常在传入之前或迭代过程中就已创建。并发限制需要额外队列、信号量或 worker pool。

## 易错点

- 用 `results.push(value)`，导致输出顺序变成完成顺序。
- 忘记 `Promise.resolve`，普通值或 thenable 处理不正确。
- 空输入时永远不 resolve。
- 只写成功回调，没有把任一 rejection 传给外层 `reject`。
- 误以为 `Promise.all` reject 后会自动取消其他异步任务。
- 把“数组版参考实现”说成题源明确要求只接受数组，或反过来把“任意 iterable”说成题干原文要求。
- 声称这份独立函数实现了原生静态方法全部构造器/子类泛化细节，而实际上没有。
