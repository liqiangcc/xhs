<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_1b54beec356cebaa5bf68b8935cb9e0a","version":1,"status":"draft","updated_at":"2026-08-22","quality_tier":"candidate","answer_type":"coding"} -->
# usePrevious：既保留上一次值，又让变化进入 React 的渲染状态

## 核心结论

原始面经连续保留了两个要求：先手写 `usePrevious` 记录 state 的上一次值，再在此基础上“让其值的改变也能触发 UI 更新”。它没有保存 Hook 的返回结构、初始 previous 值或具体组件代码。

普通 `usePrevious` 常用 `useRef`，因为 ref 能跨 render 保存值；但 React 官方文档明确说明，修改 `ref.current` **不会触发重新渲染**，因此它不满足第二个要求。如果 previous 本身参与 UI，就应把这段历史放进 React state。下面候选 API 选择：初次 render 返回 `undefined`；输入 `value` 发生 `Object.is` 意义上的变化时，把旧 `current` 变成 `previous`，并用 `setState` 让 React 立即重新 render 当前组件。

## 1 分钟版

我会先指出 follow-up 改变了数据的角色：原先 previous 只是“跨 render 保存”的值，用 ref 很自然；现在 previous 会影响 UI，就不能只改 ref，因为 React 不会感知 `ref.current` 的修改。

候选实现把 `{ current, previous }` 放进 `useState`：

```javascript
import { useState } from 'react';

export function usePrevious(value) {
  const [history, setHistory] = useState(() => ({
    current: value,
    previous: undefined,
  }));

  if (!Object.is(history.current, value)) {
    const previous = history.current;
    setHistory({ current: value, previous });
    return previous;
  }

  return history.previous;
}
```

初次调用返回 `undefined`。例如输入依次是 `1 → 2 → 3`，稳定提交后的 previous 依次是 `undefined → 1 → 2`。

## 3 分钟版

关键不是“把 `useRef` 换成 `useState`”这一句，而是不能破坏 previous 的语义。

一个容易写错的版本是：

`useEffect(() => setPrevious(value), [value])`

如果 Hook 直接返回这个 `previous` state，effect 执行后又会触发一次 render，此时返回值会变成**当前 value**，于是“上一次值”被覆盖成当前值。要同时满足“previous 正确”和“previous 改变触发 UI”，需要同时保存“最后已接受的 current”和“它之前的 previous”。

候选实现使用 React 官方 `useState` 文档中的“存储前一次 render 信息”模式：当 render 发现传入 `value` 与 state 中的 `current` 不同，就在条件分支内更新当前组件自己的 state。React 会丢弃这一轮输出并立即用新 state 重新 render 当前组件；因此最终提交的 render 中，`history.previous` 是旧 `current`，`history.current` 是新 `value`。

必须有条件判断，否则 render 中无条件 `setState` 会造成无限重渲染。这里用 `Object.is` 与 React 对 state 相等性的语义保持一致，并能正确处理 `NaN`、`-0`/`0` 这类 JavaScript 边界。

## 关键细节

- **源事实**：自定义 Hook 叫 `usePrevious`，先记录 state 的上一次值；follow-up 要求该值的改变也能触发 UI 更新。
- **候选返回 API**：只返回 previous；初始 previous 选择 `undefined`。源材料没有规定这两点，所以它们是显式实现选择。
- **为什么不用 ref 作为最终可见状态**：React 官方文档说明修改 ref 不触发 render；用于展示在 UI 的信息应放进 state。
- **为什么保存两个字段**：只保存 `previous=value` 会在触发的新 render 中把“previous”变成“current”；`{current, previous}` 才能保持历史关系。
- **为什么可以 render 中 setState**：React 官方 `useState` 文档给出了“存储前一次 render 信息”的条件更新模式；它只允许更新当前正在 render 的组件，并要求条件最终变为 false。
- **相等性**：使用 `Object.is(history.current, value)`；相同值不重复 setState，避免无意义 render 和循环。
- **对象输入边界**：对象/数组按引用做 `Object.is` 比较。若调用方每次都创建新对象，即使字段相同也会被视为新 value；是否需要深比较不是原题要求。
- **并发/Strict Mode 边界**：实现不依赖 render 次数计数，也不在 updater 中做副作用；状态对象按不可变方式替换。真实项目仍应在目标 React 版本和 Strict Mode 下跑组件测试。

## 原理机制

状态转移可以写成：

`(current=C, previous=P) + newValue=N`

- 若 `Object.is(C, N)`：状态不变，返回 `P`；
- 否则：新状态变成 `(current=N, previous=C)`，最终返回 `C`。

所以对序列 `A, B, C`：

- 初始：`{current:A, previous:undefined}` → 返回 `undefined`；
- 输入 B：更新为 `{current:B, previous:A}` → 稳定 render 返回 A；
- 输入 C：更新为 `{current:C, previous:B}` → 稳定 render 返回 B。

这个转移模型可以独立于 React 做确定性测试；React 层面的两条关键语义——“ref 更新不触发 render”和“当前组件可在条件分支中用 state 保存前一次 render 信息并立即重渲染”——由 React 官方文档提供边界证据。

## 项目经验版

原始面经没有给出真实项目中的 Hook 使用场景，因此不虚构线上经历。若落到真实组件，我会增加一个最小组件测试：把 current 和 previous 都渲染出来，连续更新 prop/state，断言 UI 从 `current=1, previous=undefined` 变为 `current=2, previous=1`，再验证 Strict Mode 下没有无限 render 或副作用重复。

## 常见追问

- 问：普通 `usePrevious` 为什么经常用 `useRef`？答：ref 可以跨 render 保存信息，又不会因为写入自身触发额外 render；如果 previous 只供下一次 render 读取，这是合适的。但本题 follow-up 明确要求变化能驱动 UI，所以需要 state。
- 问：为什么不能在 effect 里直接 `setPrevious(value)`？答：如果 Hook 返回这个 state，effect 触发的新 render 会把 previous 显示成当前 value；需要同时保存 current 和 previous，才能在重渲染后仍保持“上一次”的定义。
- 问：render 中调用 setter 不会死循环吗？答：只有无条件更新才会。这里仅当 `current` 与输入不同才 set，并把 `current` 更新成输入值；React 紧接着重渲染时条件变 false。
- 问：对象内容一样但引用不同怎么办？答：当前候选按 `Object.is` 判断，因此会认为发生变化。若业务要结构相等，需要额外比较策略，但那是新的 API 契约和性能取舍，不是原题已经规定的行为。
- 问：为什么初始返回 `undefined`？答：第一次 render 没有“上一次”值；`undefined` 是候选 API 选择，也可以设计成让调用方传初始 previous，只要明确契约即可。

## 易错点

- 继续只写 `ref.current = value`，却声称 UI 会因此自动更新。
- 把 state 直接设置成当前 value，导致 previous 在重渲染后不再是上一次。
- render 中无条件 `setState`，产生无限重渲染。
- 在状态更新逻辑里执行副作用，导致 Strict Mode/重试 render 下行为不纯。
- 把初始 previous、深比较、返回 tuple 等候选 API 选择说成原题明示要求。
