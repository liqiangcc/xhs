# Answer Batch 0020 — Repository Source Packet

This file is mechanically extracted from repository source only. It makes no answer-content inference and must be reviewed source-first before any candidate is authored.
Both caption text (`note_desc`) and image transcripts (`note_img_txt`) are included when present so structured/tagged questions can be checked against the strongest repository-local source.

## `cq_q_314a8ebf7f22e3845454fb724d41ed16`

### Canonical record

```json
{
  "aliases": [
    "算法：实现一个函数防抖的 TypeScript 版本。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_314a8ebf7f22e3845454fb724d41ed16",
  "canonical_title": "算法：实现一个函数防抖的 TypeScript 版本。",
  "companies": [
    "百度"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "primary_entities": [
    "防抖",
    "高阶函数",
    "typescript"
  ],
  "question_ids": [
    "314a8ebf7f22e3845454fb724d41ed16"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67d8d9fc00000000090144c3`

- tagged: `note_tagged/67d8d9fc00000000090144c3.json`
- caption: `note_desc/67d8d9fc00000000090144c3.txt`
- image transcript: `note_img_txt/67d8d9fc00000000090144c3.txt`

Tagged question:

```json
{
  "question_id": "314a8ebf7f22e3845454fb724d41ed16",
  "original_question": "算法：实现一个函数防抖的 TypeScript 版本。",
  "domain": {
    "l1": "其他",
    "l2": "其他"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "防抖",
    "typescript",
    "高阶函数"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
#前端面试[话题]# #面试题[话题]# #前端[话题]# #前端入门[话题]# #前端找工作[话题]# #前端知识[话题]# #大厂前端[话题]# #前端面试题[话题]# #前端开发[话题]# #前端开发工程师[话题]#
```

Image transcript:

```text
```
3.13百度前端面经

百度前端面试一面

题目
1. 解释事件循环机制及宏任务/微任务执行顺序
2. 如何实现一个深拷贝函数?
3. 请描述Vue3的响应式原理与Vue2的区别
4. CSS实现垂直居中的五种方法
5. 手写Promise.all的实现

百度前端二面

题目
1. 浏览器缓存机制及缓存策略优化
2. 如何实现前端性能监控系统?
3. 说说Webpack的HMR原理
4. 实现一个函数防抖的TypeScript版本
5. React Fiber的调度机制是怎样的?
6. 如何解决跨域问题? CORS的预检请求是什么?
7. 从输入URL到页面展示的完整过程

百度前端三面

题目
1. 前端工程化建设的具体实践方案
2. 微前端架构的优缺点及实现方案
3. 如何设计一个可维护的React组件库?
4. 前端安全防护措施(XSS/CSRF)
5. 大规模表单页面的性能优化策略
6. 说说Service Worker的缓存策略
```
```
3. Vue3响应式原理与Vue2的区别

特性 Vue2 Vue3
实现方式 Object.defineProperty Proxy
数组监听 需重写数组方法(如 直接监听数组索引和长度变化
push)
新增/删除属性 需Vue.set/Vue.delete 自动检测
性能优化 初始化递归遍历对象 惰性响应(按需触发
getter)
依赖收集 通过Dep和Watcher类 通过effect和
track / trigger
代码结构 选项式 API 组合式 API + 响应式模块化

4. CSS实现垂直居中的五种方法

1. Flex 布局
.parent {
display: flex;
align-items: center;
justify-content: center;
}

2. Grid 布局
.parent {
display: grid;
place-items: center;
}

3. 绝对定位+Transform
.child {
position: absolute;
top: 50%;
```
```
4. Table-Cell
.parent {
display: table-cell;
vertical-align: middle;
text-align: center;
}
.child {
display: inline-block;
}

5. Line-Height (单行文本)
.parent {
height: 100px;
line-height: 100px;
text-align: center;
}

5. 手写Promise.all的实现
Promise.myAll = function (promises) {
return new Promise((resolve, reject) => {
const results = [];
let count = 0;
for (let i = 0; i < promises.length; i++) {
Promise.resolve(promises[i])
.then((res) => {
results[i] = res;
count++;
if (count === promises.length) resolve(results);
})
.catch(reject); // 任一 Promise 失败则立即 reject
}
if (promises.length === 0) resolve(results); // 处理空数组
});
};

核心逻辑:
1. 遍历传入的Promise数组,用Promise.resolve包裹保证非Promise值。
2. 通过计数器统计完成的Promise数量,全部完成后返回结果数组。
3. 任一Promise失败则立即终止。

二面答案:

1. 浏览器缓存机制和缓存策略优化
浏览器缓存机制:
分为强缓存和**协商缓存”,优先级:强缓存>协商缓存。
·强缓存:
。Cache-Control(优先级高):如 max-age=3600(单位秒)、no-cache(强制协
商缓存)、no-store(不缓存)。
。Expires(HTTP/1.0):绝对时间,可能因时区或系统时间误差。

·协商缓存:
。ETag/If-None-Match(优先级高):文件内容哈希值,精确判断资源变化。
。Last-Modified/If-Modified-Since:最后修改时间,精度为秒,可能因时间误差
效。
```
```
11
});

6. 接收响应:
。解析状态码(如200、304)、响应头(缓存相关字段)、响应体(HTML)。

7. 渲染流程:
。解析HTML:构建DOM树,遇到CSS/JS会阻塞或并行下载。
。解析CSS:生成CSSOM树。
。合成Render Tree:结合DOM和CSSOM,排除不可见节点。
。布局(Layout):计算节点几何位置。
。绘制(Painting):将布局结果转换为屏幕像素。
。合成(Composite):层合并,GPU加速。

8. 加载后续资源:
。解析到、等标签时触发资源加载。

9. 交互阶段:
。JS监听事件(如点击),触发重新渲染(可能引发重排或重绘)。

优化点:
。DNS预解析()、HTTP/2多路复用、资源预加载、服务瑞
染(SSR)。

三面答案

1. 前端工程化建设的具体实践方案
核心实践:
·模块化开发:
。使用ES Module或CommonJS规范拆分代码,结合Monorepo(如Lerna、Turborepo)管
理多包依赖。
·规范化工具链:
。代码规范:ESLint+Prettier+Husky(Git Hooks)确保代码一致性。
```
```
14
12
});

·Network First:优先请求网络,失败时返回缓存(适合动态内容)。
·Stale-While-Revalidate:先返回缓存,同时后台更新缓存。
·预缓存:在install阶段缓存关键资源。
·运行时缓存:动态缓存按需资源(如API响应)。

7. 首屏加载时间优化
·资源压缩:Brotli/Gzip压缩文本资源,WebP图片格式。
·代码分割:
。React.lazy + Suspense 实现路由懒加载。
。Webpack 导入(Dynamic Import)。
·预加载/预渲染:
。

·CDN加速:静态资源分发至边缘节点。
·减少关键资源:内联关键CSS,延迟非必要JS(如埋点脚本)。

8. Node.js 事件循环与浏览器事件循环的区别
特性 浏览器事件循环 Node.js 事件循环
阶段划分 宏任务/微任务 6个阶段(Timers→
Pending→Idle/Prepare→
Poll→Check→Close)
任务优先级 微任务(Promise)优先 按阶段顺序执行,
process.nextTick 优先
```
```
优缺点:
·技术栈无关,子应用独立开发部署。
·渐进式升级,降低单体巨石应用维护成本。
·团队自治,提升开发效率。

缺点:
·通信复杂度高(CustomEvent、Props、状态管理库)。
·公共依赖冗余(如重复加载React)。
·性能损耗(子应用加载时间、样式隔离成本)。

实现方案:
·qiankun:基于路由的微前端框架,通过JS沙箱和样式隔离实现子应用独立运行。
·Module Federation (Webpack 5):动态加载远程模块,共享依赖。
·iframe:简单隔离但通信困难,适用于低耦合场景。
```
```
10
2. JSONP:利用 <script> 标签跨域特性,需服务端返回回调函数包裹的数据。
3. 代理服务器:前端请求同域代理,代理转发到目标服务器(如Nginx反向代理)。
4. postMessage:跨窗口通信,适用于iframe或新窗口。
5. WebSocket:协议本身支持跨域。

CORS 预检请求:
·触发条件:非简单请求(如PUT、DELETE、自定义头、Content-Type 非
application/x-www-form-urlencoded)。
·过程:浏览器先发送OPTIONS请求,携带Origin、Access-Control-Request-
Method 等头,服务器返回允许的方法和头字段后,再发送实际请求。

7. 从输入URL到页面展示的完整过程

1. URL 解析:
。检查输入是否是URL,否则调用搜索引擎。
。解析协议、域名、端口等。

2. DNS查询:
。浏览器缓存→系统缓存→路由器缓存→ISP DNS服务器→递归查询。

3. 建立 TCP 连接:
。三次握手(SYN→SYN-ACK→ACK),若是HTTPS则进行TLS握手(协商密钥、证书验
证)。

4. 发送HTTP请求:
。请求头携带Cookie、User-Agent、Accept等信息。

5. 服务器处理请求:
。反向代理(如Nginx)转发请求到应用服务器,生成响应。
```
```
2
7. 如何实现首屏加载时间优化?
8. Node.js事件循环与浏览器事件循环的区别
9. 前端灰度发布的实现方案
10. 解释Chrome V8引擎的垃圾回收机制

参考答案

一面:

1. 事件循环机制及宏任务/微任务执行顺序
事件循环机制:
JavaScript是单线程的,通过事件循环处理异步任务。事件循环的核心是调用栈、任务队列(宏任务
队列和微任务队列)。执行流程如下:
1. 执行同步代码,直到调用栈为空。
2. 检查微任务队列,依次执行所有微任务(如Promise.then、MutationObserver)。
3. 当微任务队列清空后,执行一个宏任务(如setTimeout、setInterval、I/O操作)。
4. 重复上述过程。

执行顺序:
·微任务优先级高于宏任务。每次事件循环中,先执行所有微任务,再执行一个宏任务。
·示例:
1 setTimeout(() => console.log('宏任务'), 0);
2 Promise.resolve().then(() => console.log('微任务'));
3 // 输出顺序:微任务→宏任务

2. 实现深拷贝函数
```
```
16
最高
I/O 处理 基于 Web APIs(如DOM、 基于 libuv 的异步I/O(文
XHR) 件、网络)
并行能力 Web Worker多线程 Cluster 模块多进程

9. 前端灰度发布的实现方案
·按用户分流:
。用户ID或设备Hash取模,控制百分比(如10%用户看到新功能)。
·按路由分发:Nginx配置不同路径指向新旧版本服务。
·特性开关(Feature Toggle):
。后端接口返回新旧标志位,前端动态渲染对应功能模块。
。结合LaunchDarkly等平台动态控制开关状态。
·AB测试:通过埋点数据对比新旧版本转化率,逐步全量。

10. Chrome V8引擎的垃圾回收机制
分代回收策略:
·新生代(Young Generation):
。Scavenge算法:将内存分为From和To空间,存活对象从From复制到To,清空From。
。对象晋升:多次存活的对象移至老生代。
·老生代(Old Generation):
。标记-清除(Mark-Sweep):遍历标记活动对象,清除未标记对象。
。标记-整理(Mark-Compact):清除后整理内存碎片。
·增量标记与并行回收:
。增量标记:将标记任务拆分为小段,避免长时间阻塞主线程。
。并行回收:利用多线程加速垃圾回收过程。
```
```
7
缓存策略优化:

1. 静态资源:设置长缓存(如 max-age=31536000),通过文件名哈希(如 main.
[hash].js)实现版本控制。
2. 动态资源:使用 no-cache 或短 max-age,配合 ETag 验证。
3. 避免缓存污染:区分公共库(单独域名)、业务代码和用户数据。
4. Service Worker:精细化控制缓存逻辑,支持离线访问。

2. 如何实现前端性能监控系统?
核心步骤:
1. 数据采集:
。性能指标:通过 Performance API 获取 FP/FCP/LCP(首次渲染/首次内容渲染/最大内
容渲染)、CLS(布局偏移)、TTI(可交互时间)。
。资源加载:performance.getEntriesByType('resource')获取资源加载耗时。
。错误监控:监听 window.onerror 和 unhandledrejection 捕获 JS 错误和未处理的
Promise异常。
。用户行为:路由切换、点击事件等。

2. 数据上报:
。方式:navigator.sendBeacon (页面卸载时可靠上报)或 XMLHttpRequest。
。优化:合并上报请求、本地缓存失败请求、采样率控制。

3. 数据存储与分析:
。使用日志系统(如ELK)存储,聚合分析慢加载、高错误率等场景。
。可视化展示(如Grafana仪表盘)。

3. Webpack的HMR原理
HMR (Hot Module Replacement):
```
```
13
3. 如何设计一个可维护的 React 组件库?
设计原则:
·原子化设计:按功能拆分基础组件(Button/Input)和复合组件(Form/Table)。
·类型安全:使用TypeScript定义Props和接口。
·文档驱动:
。Storybook可视化调试,生成组件文档。
。提供Playground示例和API描述。
·样式方案:
。CSS-in-JS (Styled-components/Emotion)或CSS Modules避免全局污染。
。主题化:通过Context或CSS Variables支持主题切换。
·测试覆盖:
。单元测试(Jest+React Testing Library)验证交互逻辑。
。快照测试确保UI一致性。
·发布管理:
。语义化版本(SemVer),通过Changesets管理版本日志。

4. 前端安全防护措施(XSS/CSRF)
XSS (跨站脚本攻击)防护:
·输入过滤:对用户输入的 <>等字符转义(如 he.js 库)。
·输出编码:根据上下文使用不同编码(HTML/JS/URL)。
·CSP (内容安全策略):通过HTTP头限制脚本来源,如:

1 Content-Security-Policy: script-src 'self' https://trusted.cdn.com

·HttpOnly Cookie:防止JS读取敏感Cookie。
```
```
8
1. 建立通信:Webpack Dev Server 通过WebSocket与客户端建立连接。
2. 文件变更:Webpack 监听文件变化,重新编译生成差异化的模块补丁(Chunk)。
3. 推送更新:通过WebSocket向客户端发送hash和chunk消息。
4. 客户端处理:
。客户端收到消息后,通过JSONP请求新的模块代码([hash].hot-update.json和
[hash].hot-update.js)。
。使用HMR Runtime对比新旧模块,替换更新的模块。
。若模块接受更新(如通过module.hot.accept声明),执行回调函数,否则刷新页面。

关键点:局部更新、状态保留、依赖关系管理。

4. 函数防抖的TypeScript版本
function debounce(func: T,
delay: number,
immediate?: boolean
): (...args: Parameters) => void {
let timeoutId: ReturnType<typeof setTimeout> | null = null;
return function (this: unknown, ...args: Parameters) {
if (immediate && !timeoutId) {
func.apply(this, args);
}
if (timeoutId) {
clearTimeout(timeoutId);
}
timeoutId = setTimeout(() => {
if (!immediate) {
func.apply(this, args);
}
timeoutId = null;
}, delay);
};
}
```
```
17
优化点:
·避免全局变量、及时解除引用、慎用闭包。
```
```
9
特性:
·支持立即执行(immediate参数)。
·泛型类型保持原函数类型推断。
·清除定时器,确保最后一次触发。

5. React Fiber的调度机制
核心目标:实现增量渲染和任务优先级调度,解决同步递归渲染导致的卡顿问题。

关键机制:
1. Fiber节点:将组件树拆解为链表结构的Fiber节点,每个节点保存组件类型、状态、副作用等信
息。
2. 可中断与恢复:
。使用requestIdleCallback(或polyfill)在浏览器空闲时间段分片执行任务。
。通过循环模拟递归,保留当前处理进度,允许中断后恢复。
3. 优先级调度:
。任务分为同步、高优先级(用户交互)、低优先级(数据请求)等。
。高优先级任务可打断低优先级任务,抢占执行。
4. 双缓存技术:
。内存中构建新的Fiber树(workInProgress),完成后替换当前树,减少页面抖动。

6. 跨域解决方案与CORS预检请求

跨域解决方案:
1. CORS (主流方案):服务器端设置响应头(如Access-Control-Allow-Origin:* )。
```
```

## `cq_q_32099ab899a15a5d7ab610c1477860e1`

### Canonical record

```json
{
  "aliases": [
    "算法：非递归且不使用额外栈空间，如何遍历二叉树？(Morris遍历)"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_32099ab899a15a5d7ab610c1477860e1",
  "canonical_title": "算法：非递归且不使用额外栈空间，如何遍历二叉树？(Morris遍历)",
  "companies": [
    "腾讯"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "树"
  },
  "primary_entities": [
    "morris traversal"
  ],
  "question_ids": [
    "32099ab899a15a5d7ab610c1477860e1"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67432048000000000703084c`

- tagged: `note_tagged/67432048000000000703084c.json`
- caption: `note_desc/67432048000000000703084c.txt`

Tagged question:

```json
{
  "question_id": "32099ab899a15a5d7ab610c1477860e1",
  "original_question": "算法：非递归且不使用额外栈空间，如何遍历二叉树？(Morris遍历)",
  "domain": {
    "l1": "算法",
    "l2": "树"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L3_Diagnostic",
  "tech_entities": [
    "morris traversal"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
一面(30mins)简历评估吧:
1.自我介绍
2.实习的项目，抛了一系列的提高性能的问题，针对项目提问(实习项目略隐私，不列出来了)
3.发的论文，论文用到的算法
4.你认为算法与业务之间有什么样的关系
5.浏览器输入URL发生了什么，讲出所有知道的内容
算法题
6.非递归遍历二叉树
7.查找数组的中间元素
8.问问题
二面(50mins)仿佛题库抽问:
1.自我介绍
2.Java的并发方式
3.synchronized和lock的区别
4.Java内存模型及GC算法
5.你理解的线程安全
6.Java 源码中的HashMap、HashTable、 ArrayList及LinkedList
7.解决Hash冲突的方法及Java8对链地址法有何优化
8.加载器双亲委派模型及破坏
9.死锁的原因及预防
10.操作系统的内存管理机制
11.进程和线程的区别
12.TCP和UDP区别
13.TCP如何保证可靠性，拥塞控制如何实现
14.用过哪些数据库，支持事务的数据库的四个特性，数据库的四个隔离级别
15.讲下跳表怎么实现的
16.哈夫曼编码是怎么回事
17.非递归且不用额外空间(不用栈)，如何遍历二叉树
18.是否可以实习19.问问题
三面 (30mins):
1.自我介绍
2.实习的项目
3.依然是: 输入URL浏览器发生了什么
4.DNS解析的域名，你直接去ping，能成功吗，它是一个web server吗
5.说说长连接是怎么回事，使用长连接有什么影响
6.个人的职业规划
7.除了项目之外，有了解过其他的开源技术吗
8.NginX如何做负载均衡
9.常见的负载均衡算法有哪些
10.一致性哈希的一致性是什么意思
11.一致性哈希是如何做哈希的
12.自己最常用的数据结构是什么
13.讲讲算法及数据结构在实习项目中的用处
14.常见的排序算法及其复杂度
15.讲讲0(nlogn) 复杂度的算法在实际工程中的用处
16.问问题
HR面(20mins):
1.自我介绍
2.实习学到了什么
3.自己的职业规划
4.评价一下腾讯的技术氛围
5.实习中有没有什么不足，现在弥补了吗
6.对阿里技术氛围有什么样的理解，用过哪些阿里的开源库
7,给你一千万创业，你怎么分配资金，自己承担什么样的角色(CEO?CTO?C00?)
8.蚂蚁金服最后待offer给你转推荐，你清楚原因吗(岗位不符合预期)
9.加上之前的面试和蚂蚁的面试，你面试与自己预期相比表现怎么样
10.期待的工作地点
11.问问题
#面经[话题]# #阿里巴巴面试题[话题]# #java[话题]# #互联网大厂[话题]# #程序员[话题]# #经验分享[话题]#
```

## `cq_q_32261275f6fd11df329bd168116d64b1`

### Canonical record

```json
{
  "aliases": [
    "算法：对先升序后降序的数组进行排序"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_32261275f6fd11df329bd168116d64b1",
  "canonical_title": "算法：对先升序后降序的数组进行排序",
  "companies": [
    "小米"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "排序"
  },
  "primary_entities": [
    "sorting"
  ],
  "question_ids": [
    "32261275f6fd11df329bd168116d64b1"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `6668516a000000000e033155`

- tagged: `note_tagged/6668516a000000000e033155.json`
- caption: `note_desc/6668516a000000000e033155.txt`
- image transcript: `note_img_txt/6668516a000000000e033155.txt`

Tagged question:

```json
{
  "question_id": "32261275f6fd11df329bd168116d64b1",
  "original_question": "算法：对先升序后降序的数组进行排序",
  "domain": {
    "l1": "算法",
    "l2": "排序"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "sorting"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
小米一面
二分查找(递归和非递归)反转链表(递归和非递归)常用Java集合类
●HashMap为什么长度是2的n次幂,数据结构,扩容(包括元素移动的细节),线程不安全的问题
●ConcurrentHashMap怎么保证线程安全,1.7和
1.8有什么变化,为什么要要这么优化
● CopyOnWriteList怎么保证线程安全,为什么这么做
● Java synchronized关键字的作用,原理,锁升级、锁粗化、锁消除
volatile关键字的作用,原理 MVCC
●事务的ACID,每一项是如何保证的
· MySQL的索引结构,为什么是B+树而不是B树
小米二面
●先升序后降序的数组排序
求递增数组中相加等于10的元素对
17^400-19100计算结果能不能被10整除
●一个url对应一个random值,要求设计-个系统，根据url查询random值,具体到表怎么设计,索引怎么
·加，代码怎么写
●讲项目,画架构图,为什么这么设计,哪一块是你做的,为什么这么做，做了多久后面的记不住了…
小米三面
●自我介绍
镜像二叉树(递归和非递归)
删除二叉搜索树的某一个节点给定数组,求第k大的数字
单例模式的几种写法,解释为什么
tcp握手挥手过程,以及socket的状态变化线程的状态,以及变化的时机
●Java内存模型,堆的组成,gc过程
·synchronized修饰同一个类的两个静态***同步吗,为什么
线程池设置了coreSize和maxSize之后,如果线程数量已经达到了coreSize,这个时候进来一个任务,会怎么处理
●SQL查询优化怎么做
●你的优点是什么,缺点是什么●最快什么时间入职,薪资要求●你有什么要问我的吗
#面经[话题]# #面试题[话题]# #小米面试[话题]# #互联网大厂[话题]# #Java[话题]# #经验分享[话题]#
```

Image transcript:

```text
我无法直接执行 `gemini` 命令来识别图片内容。我的可用工具中没有直接执行 OCR 或运行 shell 命令的功能。
```

## `cq_q_3238f5e15ec86e90f7f1a8560c854d9a`

### Canonical record

```json
{
  "aliases": [
    "代码：10进制转N进制的实现"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_3238f5e15ec86e90f7f1a8560c854d9a",
  "canonical_title": "代码：10进制转N进制的实现",
  "companies": [
    "华为"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "base conversion"
  ],
  "question_ids": [
    "3238f5e15ec86e90f7f1a8560c854d9a"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `663b7649000000001e038251`

- tagged: `note_tagged/663b7649000000001e038251.json`
- caption: `note_desc/663b7649000000001e038251.txt`
- image transcript: `note_img_txt/663b7649000000001e038251.txt`

Tagged question:

```json
{
  "question_id": "3238f5e15ec86e90f7f1a8560c854d9a",
  "original_question": "代码：10进制转N进制的实现",
  "domain": {
    "l1": "算法",
    "l2": "其他"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "base conversion"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
华为od面经分享
双非一本，三年java开发，机试257，二面挂了，分享下整个过程给大家参考：
一、11月3号完成机试，两道简单都ac了，最后一题只通过一点：
第一道题目考查的是10进制转换其他进制
第二题是给一个数组，找出这个数组中的众数(众数可能不止一个)，然后输出众数中的中位数
第三题题目是<数据单元的变量替换>,题目太长就不说了，感兴趣的可以自己搜索下
二、11月6日完成性格测试
三、11月10号完成HR面，相关问题如下：
1、离职原因，需要详细说明
2、讲一个最能体现你个人能力的项目
3、你认为这个项目里面对你带来最大收获的是什么
4、除了上述你说的问题外，在项目交付的时候还遇到那些问题吗？在这过程当中你负责什么？
5、有没有遇到定位时间特别长，客户压力大，你也压力大的那种场景？在整个过程中你印象最深刻的是什么？比较深刻是因为什么？
6、通过这个事情对你日常工作有什么影响？
7、事后再开发产品方面有什么动作吗？结果如何？
8、对od的用户模式了解多少？
9、平常有什么兴趣爱好？(指业余时间你投入比较多时间并长期去做的一件事)
10、这个爱好给你带来了什么？
四、11月12日技术一面，面试官挺好的，在面试过程中一直引导，做算法题的时候也给了提示，项目问题就不写了，其他问题如下：
1、arrayList是怎么实现动态数组的？
2、jdk1.8默认的垃圾收集器是什么？使用的什么算法？
3、jdk13、jdk17新特性？
4、volitail关键字的作用，和锁比起来性能如何？
5、hashMap存取数据的时间复杂度是多少？
6、java面向对象的设计原则是什么？
算法题:三选一
1、将堆抽象成类，实现获取元素、删除元素等的操作方法
2、给定一个字符串的算术表达式(包含加减乘除括号，0-9数字组合而成)，输出算术表达式的值
3、某国只有1分、2分、3分的硬币，请计算出将N分硬币兑换成该国硬币的所有方式
五、11月13日技术面试二面，二面给我的感觉是面试官比较看重你私底下有没有去研究、去学习你在使用的这些框架，如果平时只注重实现业务功能的话，面试的时候就比较难受了，比如我，本轮面试很多问题答不出来，题也没有解出来，相关问题如下：
1、在springboot启动阶段或者初始阶段去获取外部的配置数据来启动项目，怎么去实现？
2、你会怎么去开发一个starter，运用了springboot的什么机制？
3、讲讲引入一个mysql的starter或者kafka的starter，他是怎么去加载的？启动原理是什么？
#Java[话题]##华为od[话题]# #华为面经[话题]# #面经分享[话题]#
```

Image transcript:

```text
晚上8:53 | 3.8K/s♡
3/3
9、怎么优化一个慢SQL?
10、explain的结果有哪些,有哪些信息去告诉你怎么优化?
11、分享一个你在项目里面实现的解决方案?
算法题:
给它一个边长为len的表格,把它按边长gridLen来划分为若干等分的格栅。(len
为gridLen的整数倍长)。
*请计算进行格栅化之后,给定的坐标(x,y)出了于第几个格栅。格栅编号从1开始
*如:以下为边长6的表格,格栅边长为3,其中(1,5)出于第二个格栅。输出2
六、以上就是本次面试的相关问题,仅供各位参考,希望各位想去od的小伙伴能
顺利入职。

https://csproject.icu/index.php/269.html
这一个网页
晚上8:53 | 1.7K/s♡
2、jdk1.8默认的垃圾收集器是什么?使用的什么算法?
3、jdk13、jdk17新特性?
4、volitali关键字的作用,和锁比起来性能如何?
5、hashMap存取数据的时间复杂度是多少?
6、java面向对象的设计原则是什么?
算法题:三选一
1、将堆抽象成类,实现获取元素、删除元素等的操作方法
2、给定一个字符串的算术表达式(包含加减乘除括号,0-9数字组合而成),输出
算术表达式的值
3、某国有1分、2分、3分的硬币,请计算出将N分硬币兑换成该国硬币的所有
方式
五、11月13日技术面试二面,二面给我的感觉是面试官比较看重你私底下有没有
去研究、去学习你在使用的这些框架,如果平时只关注实现业务功能的话,面试
的时候就比较难受了,比如我,本轮面试很多问题答不出来,题也没有解出来,
相关问题如下:
1、在springboot启动阶段或者初始阶段去获取外部的配置数据来启动项目,怎
么去实现?
2、你会怎么去开发一个starter,运用了springboot的什么机制?
3、讲讲引入一个mysql的starter或者kafka的starter,他是怎么去加载的?启
动原理是什么?
4、列举几个springboot的监听器,分别起到什么作用?
5、前端开发进度条,后端人员应该开发那些接口去实现这个功能?
6、请求头里面有哪些信息?
7、union和union all的区别是什么?
8、左连接和右连接的区别?

9、怎么优化一个慢SQL?
10、explain的结果有哪些,有哪些信息去告诉你怎么优化?
11、分享一个你在项目里面实现的解决方案?
晚上8:53 | 0.0K/s♡
华为od面试分享
双非一本,三年java开发,机试257,二面挂了,分享下整个过程给大家参考:
一、11月3号完成机试,两道简单都ac了,最后一题只通过一点:
第一道题目考查的是10进制转换其他进制
第二题是给一个数组,找出这个数组中的众数(众数可能不止一个),然后输出众
数中的中位数
第三题题目是<数据单元的变量替换>,题目太长就不说了,感兴趣的可以自己搜索
下
二、11月6日完成性格测试
三、11月10号完成HR面,相关问题如下:
1、离职原因,需要详细说明
2、讲一个最能体现你个人能力的项目
3、你认为这个项目里面对你带来最大收获的是什么
4、除了上述你说的项目问题外,在项目交付的时候还遇到那些问题吗?在这个过程当中
你负责什么?
5、有没有遇到定位时间特别长,客户压力大,你压力也大你的那种场景?在整个过
程中你印象最深刻的是什么?比较深刻是因为什么?
6、通过这个事情对你日常工作有什么影响?
7、事后事再开发产品方面有什么动作吗?结果如何?
8、对od的用户模式了解多少?
9、平常有什么兴趣爱好吗?(指业余时间你投入比较多时间并长期去做的一件事)
10、这个爱好给你带来了什么?
四、11月12日技术一面,面试官挺好的,在面试过程中一直引导,算法题的时候
候也给了提示,项目问题就不写了,其他问题如下:
1、arrayList是怎么实现动态数组的?
```

## `cq_q_3395e0de3268979e86446a8ad2eebb4b`

### Canonical record

```json
{
  "aliases": [
    "算法：力扣 135. 分发糖果？"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_3395e0de3268979e86446a8ad2eebb4b",
  "canonical_title": "算法：力扣 135. 分发糖果？",
  "companies": [
    "字节跳动"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "greedy"
  ],
  "question_ids": [
    "3395e0de3268979e86446a8ad2eebb4b"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68a3331f000000001b022d68`

- tagged: `note_tagged/68a3331f000000001b022d68.json`
- caption: `note_desc/68a3331f000000001b022d68.txt`

Tagged question:

```json
{
  "question_id": "3395e0de3268979e86446a8ad2eebb4b",
  "original_question": "算法：力扣 135. 分发糖果？",
  "domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "greedy"
  ],
  "business_context": [
    "LeetCode 135"
  ],
  "is_valid_for_library": true
}
```

Caption text:

```text
27min
实习内容介绍
协程池内部实现原理是什么
一个RPC接口调用QPS上限为y, 通过协程池调用这个RPC接口，协程池设定并发协程数量上限多少
根据RPC接口响应时间t，协程数量 = y * t
Redis你一般用什么数据结构
多机房的Redis分布式锁极端情况下会出现什么问题，怎么解决多机房数据一致性问题

10min
RocketMq和Kafka区别
消息队列的消息堆积怎么解决
消息队列lazy、Rebalance问题
消息队列消费幂等性

10min
用户输入网址到返回内容中间经历了什么
网关怎么找到后端的服务器
访问出错怎么排查问题

18min
编程
分发糖果
#后端开发[话题]# #互联网大厂[话题]# #大厂[话题]# #面经[话题]#
```

## `cq_q_339b8eac64f281ce9f9ff7268db622ba`

### Canonical record

```json
{
  "aliases": [
    "算法：给你一个图的邻接矩阵，请你对这个图进行深度优先遍历"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_339b8eac64f281ce9f9ff7268db622ba",
  "canonical_title": "算法：给你一个图的邻接矩阵，请你对这个图进行深度优先遍历",
  "companies": [
    "快手"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "访问标记数组",
    "邻接矩阵",
    "图遍历",
    "dfs"
  ],
  "question_ids": [
    "339b8eac64f281ce9f9ff7268db622ba"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `6892d5250000000023020667`

- tagged: `note_tagged/6892d5250000000023020667.json`
- caption: `note_desc/6892d5250000000023020667.txt`
- image transcript: `note_img_txt/6892d5250000000023020667.txt`

Tagged question:

```json
{
  "question_id": "339b8eac64f281ce9f9ff7268db622ba",
  "original_question": "算法：给你一个图的邻接矩阵，请你对这个图进行深度优先遍历",
  "domain": {
    "l1": "算法与数据结构",
    "l2": "树/图"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "N_A",
  "tech_entities": [
    "dfs",
    "邻接矩阵",
    "图遍历",
    "访问标记数组"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
实习经历提问（约20min）
Java的锁介绍一下
aqs原理
有哪些锁用到了aqs
cms和g1垃圾回收器有什么区别
有进行过jvm调参嘛？为什么要进行这样的调参
介绍一下spring boot的启动过程（完全不知道啊）
tcp粘包说一下，如何解决？
tcp4次挥手
数据处理
有100亿个url，怎么找到相同的url
算法
给你一个图的邻接矩阵
请你对这个图进行深度优先遍历
反问：什么业务
感觉有点凉了，手撕没有撕出来，一些问题答的也不好
#互联网大厂[话题]#  #面经[话题]# #面试[话题]# #秋招人的精神状态[话题]#
```

Image transcript:

```text
--- 图片 1 ---

快手秋招
一面凉经

[图像摘要：浅绿色背景，包含引号装饰，居中显示标题“快手秋招 一面凉经”。这似乎是一份关于快手面试经验的分享笔记封面。]
```

## `cq_q_33d091345ac48812c61f235d00515560`

### Canonical record

```json
{
  "aliases": [
    "算法 1：火柴拼三角形。给定一个火柴长度数组，判断是否能拼成一个等边或普通三角形，并找出最长周长"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_33d091345ac48812c61f235d00515560",
  "canonical_title": "算法 1：火柴拼三角形。给定一个火柴长度数组，判断是否能拼成一个等边或普通三角形，并找出最长周长",
  "companies": [
    "京东"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "双指针/滑动窗口"
  },
  "primary_entities": [
    "greedy algorithm"
  ],
  "question_ids": [
    "33d091345ac48812c61f235d00515560"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67f0ff86000000001c0283b9`

- tagged: `note_tagged/67f0ff86000000001c0283b9.json`
- caption: `note_desc/67f0ff86000000001c0283b9.txt`
- image transcript: `note_img_txt/67f0ff86000000001c0283b9.txt`

Tagged question:

```json
{
  "question_id": "33d091345ac48812c61f235d00515560",
  "original_question": "算法 1：火柴拼三角形。给定一个火柴长度数组，判断是否能拼成一个等边或普通三角形，并找出最长周长",
  "domain": {
    "l1": "算法",
    "l2": "数组"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "greedy algorithm"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
📝京东的流程是所有厂中最慢的，基本上节奏是一周一面，京东这个部门base是上海，已oc并且拒掉了。最大的体验是两轮技术面算法都不是hot100的原题，一面在本地ide完成，二面在word中写。

⭕️一面
💡自我介绍
1️⃣询问到岗日期
2️⃣职业规划
3️⃣面试官介绍部门

💡项目技术栈及实现
1️⃣负载均衡的常见算法？
2️⃣nacos实现的原理？
3️⃣监听器如何和nacos通信？
4️⃣jwt吊销怎么办？有没有无存储的方案？
5️⃣项目难点？亮点？介绍具体实现要点
💡spring框架
1️⃣spring的aop？怎么实现的？
2️⃣ioc是什么？具体？
3️⃣bean注入的方式？
💡Java、JUC、JVM
1️⃣hashmap和concurrent hashmap的区别？初始和扩容有区别吗？
2️⃣java的四种引用类型？使用场景？
3️⃣weak hashmap如何理解和使用？
4️⃣jvm cms和g1的区别？
5️⃣8g新生代和老年代怎么配置
6️⃣线程池类型及其区别？CompleteFuture使用哪种线程池？
7️⃣策略模式是什么？
💡算法手撕
1️⃣找到最长的区间火柴拼成一个三角形
2️⃣滑动窗口20分钟解决运行调试输出正确结果后，面试官问如果可以打乱顺序怎么优化（排序）

⭕️二面
八股较少，简单问了几个我答得很深后面就没问了，面试官看起来很忙，一边面试一边做他自己的事情，后面一直在写算法题，在word里写的很不习惯写了很久，所幸最后还是通过了。
1️⃣ java中怎么线程同步？并发问题？
2️⃣sync具体怎么用？
3️⃣简要回答，hashmap是线程安全的吗？多线程环境下怎么使用hashmap
4️⃣有一个二维数组，每一行只有0，1，每一行排序，最小的时间复杂度内，找出哪一行的1最多（在word中写）#oc[话题]# #java[话题]# #后端开发[话题]# #计算机[话题]# #互联网大厂[话题]# #程序员[话题]# #京东[话题]#
```

Image transcript:

```text
我无法直接识别图片中的文本。我没有提供识别图片内容的工具。
```

## `cq_q_349bf213858328393da46111a614d286`

### Canonical record

```json
{
  "aliases": [
    "算法：LeetCode 49. 字母异位词分组（Group Anagrams）。除了哈希表法，是否还了解其他优化思路？"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_349bf213858328393da46111a614d286",
  "canonical_title": "算法：LeetCode 49. 字母异位词分组（Group Anagrams）。除了哈希表法，是否还了解其他优化思路？",
  "companies": [
    "网易云音乐"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "其他"
  },
  "primary_entities": [
    "哈希表",
    "字母异位词"
  ],
  "question_ids": [
    "349bf213858328393da46111a614d286"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `67dd34b2000000001d021316`

- tagged: `note_tagged/67dd34b2000000001d021316.json`
- caption: `note_desc/67dd34b2000000001d021316.txt`
- image transcript: `note_img_txt/67dd34b2000000001d021316.txt`

Tagged question:

```json
{
  "question_id": "349bf213858328393da46111a614d286",
  "original_question": "算法：LeetCode 49. 字母异位词分组（Group Anagrams）。除了哈希表法，是否还了解其他优化思路？",
  "domain": {
    "l1": "算法",
    "l2": "其他"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "哈希表",
    "字母异位词"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
⭕一面 35min：
自我介绍
1. java中的锁，说说synchronized底层原理。
2. 线程池参数，过期时间的意义，超出核心线程数的会被回收吗，非核心线程会被回收吗？怎么判断他要不要回收，怎么知道他过期了的。那我创建十个线程，1~10,核心数8个，9和10还在执行任务，1~8不执行了，这时候会怎么做。
说说线程池的阻塞队列有什么用，为什么用阻塞队列不用普通队列，在并发情况下，往队列中加任务不会有线程安全问题吗。
3. 说说AQS，有什么用。ReentrantLock怎么实现公平和非公平，如果多个线程同时lock怎么处理线程安全问题。
4. 说说CAS，旧值存储在哪里？
5. 对哪个框架比较熟悉。说说MyBatis的xml文件到mapper最后查到内容的过程。
6. redis的过期淘汰策略，内存不足淘汰策略，redis的LRU是怎么做的
7. 说说双亲委派机制，以及为什么。
8. 实习相关
9. 项目相关。
10 算法lc49，用的哈希表，问还有什么其他方法（不会）
11. 反问

最后还谢谢我的面试，感觉寄

补充：
1.封装和多态
2. linux中如何查找日志中指定字符串在哪一行

.
内容来自牛友：全都一面挂
来源：牛客

#网易云音乐[话题]# #java[话题]# #求职[话题]# #实习[话题]# #牛客社区[话题]# #牛客app[话题]# #面试笔试抄作业[话题]# #互联网大厂[话题]#
```

Image transcript:

```text
我无法直接识别图片中的文本。但是，我看到你已经在“Content from referenced files”部分提供了图片中的文字内容。我将输出这些内容：

牛可乐
完成
小米 - java面试经验
一面 35min:
自我介绍
1. java中的锁，说说synchronized底层原理。
2. 线程池参数，过期时间的意义，超出核心线程数的会被
回收吗，非核心线程会被回收吗？怎么判断他要不要回
收，怎么知道他过期的。那我创建十个线程，1~10，核心
数8个，9和10还在执行任务，1~8不执行了，这时候会怎
么做。
说说线程池的阻塞队列有什么用，为什么用阻塞队列不用
普通队列，并在并发情况下，往队列中加任务会不会有线程安
全问题吗。
3. 说说AQS，有什么用。ReentrantLock怎么实现公平和
非公平，如果多个线程同时lock怎么处理线程安全问题。
4. 说说CAS，旧值存储在哪里？
5. 对哪个框架比较熟悉。说说MyBatis的xml文件到
mapper最后查到内容的过程。

牛可乐
完成
6. redis的过期淘汰策略，内存不足淘汰策略，redis的LRU
是怎么做的
7. 说说双亲委派机制，以及为什么。
8. 实习相关
9. 项目相关。
10 算法lc49，用的哈希表，问还有什么其他方法（不会）
11. 反问

最后还谢谢我的面试，感觉寄

补充:
1.封装和多态
2. linux中如何查找日志中指定字符串在哪一行

内容来自牛友: 全都一面挂
来源: 牛客
指路:
全都一面挂 出师牛
03-13 11:17 已编辑
小米java一面
```

## `cq_q_3523542f7ad2ae207715d1fb093c861f`

### Canonical record

```json
{
  "aliases": [
    "算法手撕：最小包含全部 n 种颜色的连续子序列（长度为 m 的环形数组，双指针/滑动窗口）。"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_3523542f7ad2ae207715d1fb093c861f",
  "canonical_title": "算法手撕：最小包含全部 n 种颜色的连续子序列（长度为 m 的环形数组，双指针/滑动窗口）。",
  "companies": [
    "未知"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "操作系统",
    "l2": "其他"
  },
  "primary_entities": [
    "滑动窗口",
    "环形数组",
    "双指针"
  ],
  "question_ids": [
    "3523542f7ad2ae207715d1fb093c861f"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `68caa7b0000000000e02205d`

- tagged: `note_tagged/68caa7b0000000000e02205d.json`
- caption: `note_desc/68caa7b0000000000e02205d.txt`

Tagged question:

```json
{
  "question_id": "3523542f7ad2ae207715d1fb093c861f",
  "original_question": "算法手撕：最小包含全部 n 种颜色的连续子序列（长度为 m 的环形数组，双指针/滑动窗口）。",
  "domain": {
    "l1": "计算机基础",
    "l2": "算法"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "滑动窗口",
    "双指针",
    "环形数组"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
岗位：研发工程师JAVA
1、自我介绍
2、介绍实习项目解决的具体问题是什么
3、日志按等级输出的话，如何区分日志分别属于info、warning、debug哪个等级呢
4、你这个项目的功能（日志器）需要开发吗，Linux里面可以直接用shell实现这些功能吧？
5、如何理解mcp的，他主要解决什么问题，他这个协议的发展现状有什么问题吗，哪些地方可以优化呢
6、mcp的api和普通大模型的api有什么区别呢
7、sse是什么呢，如何实现的呢，在调用过程中他具体做了什么
8、一个普通的api，如何把他mcp化
9、手撕：有一个长度为m的环形小球序列，这些小球一共有n种颜色，找到最小的连续小球序列，使得序列中的小球包含全部n中颜色（用双指针）
10、反问

面试官没有开摄像头，本来就不会，更答的没底气了[捂脸R][捂脸R]

#面经[话题]# #大厂[话题]# #互联网大厂[话题]# #校招[话题]# #面试[话题]# #秋招人的精神状态[话题]# #后端开发[话题]# #秋招[话题]#
```

## `cq_q_3534d96489fb54811065d18d51bf1e5b`

### Canonical record

```json
{
  "aliases": [
    "算法：给定一列数组如[(1,4),(3,5),(1,3),(5,2)]，前一个元素为父节点后一个为子节点，构建二叉树并前序遍历"
  ],
  "answer_status": "needs_update",
  "canonical_id": "cq_q_3534d96489fb54811065d18d51bf1e5b",
  "canonical_title": "算法：给定一列数组如[(1,4),(3,5),(1,3),(5,2)]，前一个元素为父节点后一个为子节点，构建二叉树并前序遍历",
  "companies": [
    "拼多多"
  ],
  "frequency": 1,
  "primary_domain": {
    "l1": "算法与数据结构",
    "l2": "树"
  },
  "primary_entities": [
    "二叉树",
    "前序遍历",
    "树构建"
  ],
  "question_ids": [
    "3534d96489fb54811065d18d51bf1e5b"
  ],
  "review_priority": "P2",
  "schema_version": "canonical_question.v1"
}
```

### Source hits (1)

#### Source 1: `656de8b6000000001502f038`

- tagged: `note_tagged/656de8b6000000001502f038.json`
- caption: `note_desc/656de8b6000000001502f038.txt`
- image transcript: `note_img_txt/656de8b6000000001502f038.txt`

Tagged question:

```json
{
  "question_id": "3534d96489fb54811065d18d51bf1e5b",
  "original_question": "算法：给定一列数组如[(1,4),(3,5),(1,3),(5,2)]，前一个元素为父节点后一个为子节点，构建二叉树并前序遍历",
  "domain": {
    "l1": "算法",
    "l2": "树"
  },
  "question_type": "算法手撕_Coding",
  "cognitive_depth": "L2_Mechanism",
  "tech_entities": [
    "二叉树",
    "前序遍历",
    "树构建"
  ],
  "business_context": [],
  "is_valid_for_library": true
}
```

Caption text:

```text
分享拼多多社招面试-Java开发工程师
【总结】整体面试流程比较短，技术面一共就两面，而且全程不问八股文，就是看你个人写代码能力。
1. 一面会了解项目细节，然后就是一道算法题，全程会关注代码实现细节以及代码规范。
2. 二面也是看写代码能力，一道算法题，关注代码实现的细节和代码规范。
3. HR面，重点在于是否能接受加班，拼多多一般都是11 11 6。[微笑R]

#程序员面试[话题]#  #面试技巧[话题]#  #拼多多[话题]#  #拼多多面试[话题]#  #Java面试[话题]#  #程序员[话题]#  #面经[话题]#  #面试有秘招[话题]#  #互联网[话题]#
```

Image transcript:

```text
拼多多Java开发工程师

一面
1. 项目
    a. 项目介绍
    b. 会从里面挑一些细节去问, 比如问我cache, redis集群是怎么部署的, 有多少台机器, qps多少.
    c. 项目出现过什么线上问题吗? 怎么排查的? 平时会关注哪些指标?
2. 算法, 实现一个RandomSet
    // 要求实现一个RandomSet 分别实现一下方法, 并保证每一个操作都是O(1)的复杂度
    public void set(int a) {
    }
    public void remove(int a) {
    }
    public boolean contains(int a) {
    }
    public int randomGet() {
    }
    // 从RandomSet集合中等概率的随机获取一个元素。

拼多多Java开发工程师

二面
1. 项目 (和一面差不多)
2. 算法, 给定一列数组, 比如 [(1,4), (3,5), (1,3), (5,2)], 规定前一个元素为父节点, 后一个元素为子节点, 构建一个二叉树, 并前序遍历这颗二叉树。如下图
   ```
       1
      / \
     4   3
    /     \
   2       5
   ```
3. 问一些基本信息, 能不能加班压力大会怎么样?
4. 有什么优点和缺点
5. 有什么需要问我的吗?

拼多多Java开发工程师

HR面
1. 来上海工作有问题吗?
2. 是否能接受加班? 每周只休一天.
3. 未来职业规划?
4. 期望薪资多少?
```
