#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { loadCanonicalQuestions } = require('../lib/canonical_store');
const { loadQuestions } = require('../lib/question_store');
const { answerPath, readAnswerFile } = require('../lib/answer_store');
const { ensureDir } = require('../lib/io');

const ROOT = path.resolve(__dirname, '..', '..');
const GENERATOR_VERSION = 'long_tail.v1';

const KNOWLEDGE_PACKS = [
    {
        pattern: /hashmap|哈希表/,
        conclusion: 'HashMap 以数组加桶内链表/红黑树组织键值对，平均查找和写入为 O(1)；作答要同时说明哈希定位、冲突处理、扩容、树化条件以及它不是线程安全容器。',
        facts: ['JDK 8 的桶下标由扰动后的 hash 与 table 长度掩码计算。', '链表长度达到 8 且数组容量至少 64 时才会树化，否则优先扩容。', '默认负载因子 0.75 是空间与冲突概率的折中；扩容通常翻倍并重新分布节点。'],
        mechanism: 'put 先计算 hash 和桶位置，再处理空桶、同 key 覆盖或冲突追加；扩容时利用旧容量对应的 hash 位把节点拆到原位置或原位置加旧容量。',
    },
    {
        pattern: /concurrenthashmap/,
        conclusion: 'ConcurrentHashMap 的重点是并发读写下的桶级协调：JDK 8 通过 volatile、CAS 和 synchronized 协作，读路径通常不加互斥锁，扩容可由多个线程协助完成。',
        facts: ['JDK 8 不再使用 Segment 分段锁作为主结构。', '空桶初始化常用 CAS，非空桶更新在桶头上同步。', 'size 是分散计数后汇总的近似瞬时值，不能把它当作跨操作事务边界。'],
        mechanism: '节点和表引用的可见性由 volatile 保证；CAS 处理无竞争状态转换，发生桶冲突时缩小同步范围，扩容期间通过转移标记让其他线程协助迁移。',
    },
    {
        pattern: /线程池|threadpoolexecutor|executor/,
        conclusion: '线程池通过复用线程、限制并发和排队来隔离资源；回答要串起 corePoolSize、队列、maximumPoolSize、keepAliveTime、线程工厂和拒绝策略的提交顺序。',
        facts: ['提交顺序通常是先补核心线程，再入队，队列满后补到最大线程数，最后触发拒绝策略。', 'CPU 密集型侧重控制可运行线程数，IO 密集型需结合等待/计算比和下游容量估算。', '无界队列会使 maximumPoolSize 失去扩容作用，并把过载风险转成内存与延迟风险。'],
        mechanism: 'Worker 同时表示工作线程和运行状态，主锁保护 workers 集合；ctl 把运行状态与线程数量编码在一个原子整数中以协调并发状态转换。',
    },
    {
        pattern: /synchronized|锁升级|偏向锁|轻量级锁|重量级锁|mark word/,
        conclusion: 'synchronized 依靠对象监视器和 JVM 锁实现保证互斥与可见性；版本敏感点要单独说明，现代 JDK 已移除偏向锁，不能把旧版锁升级路径当成所有版本的固定结论。',
        facts: ['进入和退出监视器形成 happens-before，既提供互斥也提供内存可见性。', '无竞争或轻度竞争路径会尽量避免阻塞，持续竞争时可能膨胀为监视器并涉及线程挂起。', '锁状态、对象头布局和优化策略需绑定具体 JDK 版本验证。'],
        mechanism: '对象头中的 Mark Word、栈上锁记录与 ObjectMonitor 共同表达不同竞争状态；JIT 还可能执行锁消除和锁粗化。',
    },
    {
        pattern: /volatile|jmm|内存屏障|happens-before|指令重排/,
        conclusion: 'volatile 保证对同一变量写后读的可见性和一定的有序性，但复合读改写仍不具备原子性；解释时应落到 JMM happens-before 与编译器/处理器屏障。',
        facts: ['volatile 写 happens-before 后续对同一变量的 volatile 读。', 'i++ 包含读、计算、写，volatile 不能把三步合成原子操作。', '发布对象时仍需避免 this 逸出，并用 final、锁或安全发布规则保证完整初始化。'],
        mechanism: '编译器在 volatile 访问周围插入对应屏障并生成满足平台内存模型的指令，限制危险重排并促使其他线程观察到写入。',
    },
    {
        pattern: /\bcas\b|compareandset|aba|原子类/,
        conclusion: 'CAS 是“比较期望值并条件写入”的原子读改写，适合短临界区和低冲突更新；高竞争会自旋浪费 CPU，并需单独处理 ABA、饥饿和复合状态一致性。',
        facts: ['CAS 成功依赖内存位置仍等于期望值。', 'AtomicStampedReference 可把版本号与引用一起比较以识别 ABA。', 'LongAdder 用分散热点换取高并发吞吐，但 sum 不是跨并发更新的线性化快照。'],
        mechanism: 'Java 原子类通过 VarHandle/Unsafe 映射到底层原子指令；失败方重读状态并重试，退避和竞争分散决定高并发表现。',
    },
    {
        pattern: /\baqs\b|reentrantlock|countdownlatch|semaphore/,
        conclusion: 'AQS 用一个同步状态和 FIFO 等待队列抽象独占/共享获取；子类定义状态获取与释放语义，框架负责排队、阻塞、唤醒和取消。',
        facts: ['独占模式典型代表是 ReentrantLock，共享模式包括 Semaphore 和 CountDownLatch。', 'Condition 有独立等待队列，signal 后节点还需转移到同步队列重新竞争锁。', '公平模式尊重队列前驱，非公平模式允许插队，通常吞吐更高但等待方差更大。'],
        mechanism: '获取失败的线程进入 CLH 变体双向队列并通过 LockSupport 挂起；释放成功后唤醒合适后继，后继再竞争同步状态。',
    },
    {
        pattern: /threadlocal/,
        conclusion: 'ThreadLocal 把值放在线程自身的 ThreadLocalMap 中实现线程隔离；在线程池场景必须在 finally 中 remove，避免旧值串请求和长期引用。',
        facts: ['Map 的 key 是 ThreadLocal 弱引用，value 不是弱引用。', 'key 被回收后 value 仍可能存活到槽位清理或线程结束。', 'ThreadLocal 解决隔离，不解决跨线程传递和共享数据一致性。'],
        mechanism: '每个 Thread 持有自己的开放寻址 Map，访问按 ThreadLocal 的散列定位；set/get 会顺带清理部分失效槽位。',
    },
    {
        pattern: /arraylist|linkedlist|copyonwritearraylist|集合/,
        conclusion: '集合选型应按访问模式、修改频率、并发要求和内存成本决定，不能只背复杂度；ArrayList 擅长随机访问，LinkedList 的节点定位仍是 O(n)，CopyOnWriteArrayList 适合读多写极少。',
        facts: ['ArrayList 扩容会分配新数组并复制元素。', 'LinkedList 在已拿到节点后插删是 O(1)，按下标定位不是 O(1)。', 'CopyOnWriteArrayList 写时复制整份数组，迭代器看到稳定快照但数据可能不是最新。'],
        mechanism: '连续数组利用局部性换取扩容复制，链式结构用额外指针换取节点级插删，写时复制通过发布新数组避免读锁。',
    },
    {
        pattern: /jvm|运行时.*区|虚拟机栈|堆|方法区|元空间/,
        conclusion: 'JVM 运行时数据区要区分线程私有的程序计数器、虚拟机栈、本地方法栈，与线程共享的堆和方法区语义；排障时再映射到堆、Metaspace、直接内存和线程栈等实际资源。',
        facts: ['对象主要分配在堆，局部变量和调用帧位于线程栈。', 'Metaspace 使用本地内存承载类元数据，不等于 Java 堆。', '不同 OOM 文案对应不同资源，不能看到 OOM 就只扩大堆。'],
        mechanism: '类加载建立类型元数据，方法调用压入栈帧，对象由分配器进入堆或经优化消除；GC 主要管理堆内对象可达性。',
    },
    {
        pattern: /\bgc\b|垃圾回收|full gc|cms|g1|zgc|三色标记/,
        conclusion: 'GC 回答应串起可达性判定、分代/分区布局、并发标记、对象转移和停顿来源；选收集器要在吞吐、延迟、堆规模与 JDK 版本之间权衡。',
        facts: ['GC Roots 包括活动线程栈、静态引用、JNI 引用等。', 'CMS 主要并发清除且有碎片和浮动垃圾问题；G1 按 Region 回收收益选择集合。', '频繁 Full GC 要先用日志、堆直方图和 dump 判断分配速率、晋升失败、泄漏或元数据问题。'],
        mechanism: '标记器从根遍历对象图；并发标记需用写屏障记录引用变化，随后在安全点完成必要修正，再清除或转移存活对象。',
    },
    {
        pattern: /classloader|类加载|双亲委派/,
        conclusion: '类加载经历加载、链接和初始化，双亲委派优先让父加载器尝试定义类，以维持核心类型唯一性和隔离边界；SPI、容器和热部署会有受控打破。',
        facts: ['链接包括验证、准备和解析；类变量显式赋值通常发生在初始化。', '类的身份由全限定名和定义它的 ClassLoader 共同决定。', '线程上下文类加载器让父层框架能够发现子层应用提供的 SPI 实现。'],
        mechanism: 'loadClass 负责委派和查找，findClass 承担自定义字节来源，defineClass 把字节定义到指定加载器命名空间。',
    },
    {
        pattern: /spring.*bean|bean.*生命周期|ioc|循环依赖|beanpostprocessor/,
        conclusion: 'Spring Bean 从 BeanDefinition 出发，经历实例化、属性填充、Aware、前后置处理、初始化和销毁；BeanPostProcessor 是代理与容器扩展的关键位置。',
        facts: ['构造器循环依赖不能由经典三级缓存方案解决。', '单例 setter/字段循环依赖可通过早期引用处理，但不应把它当作推荐设计。', '初始化后拿到的对象可能是 AOP 代理而不是原始实例。'],
        mechanism: 'BeanFactory 依据 BeanDefinition 创建对象，单例缓存协调完整实例、早期引用和对象工厂；后置处理器可在初始化前后替换返回对象。',
    },
    {
        pattern: /\baop\b|动态代理|cglib|jdk.*代理/,
        conclusion: 'Spring AOP 通过代理把通知织入方法调用链；JDK 动态代理基于接口，CGLIB 通过生成子类代理，self-invocation 绕过代理是事务和切面失效的常见原因。',
        facts: ['final 类或 final 方法限制基于子类的代理。', '只有经过代理对象的方法调用才会进入拦截器链。', '切点范围过大、通知顺序不清和异常吞噬会增加运行时风险。'],
        mechanism: '容器创建代理并把 Advisor 解析为拦截器链，调用时按链执行前置、目标方法、返回或异常通知。',
    },
    {
        pattern: /spring.*事务|transactional|传播.*事务|required_new/,
        conclusion: 'Spring 声明式事务通常由代理拦截建立事务边界；回答要说明传播行为、隔离级别、回滚规则、连接绑定，以及自调用、异常被吞和非代理对象导致的失效。',
        facts: ['REQUIRED 加入现有事务或新建事务，REQUIRES_NEW 挂起外层并开启独立事务。', '默认通常对 RuntimeException 和 Error 回滚，受检异常需按配置处理。', '数据库事务不能自动覆盖远程调用、消息和缓存副作用。'],
        mechanism: '事务拦截器从平台事务管理器获取资源，把连接等绑定到当前执行上下文，目标方法结束后按异常与规则提交或回滚。',
    },
    {
        pattern: /spring\s*mvc|dispatcherservlet|handlermapping/,
        conclusion: 'Spring MVC 的主链路是 DispatcherServlet 接收请求，HandlerMapping 找处理器，HandlerAdapter 调用 Controller，再经参数解析、返回值处理和异常解析生成响应。',
        facts: ['拦截器围绕 Handler 执行，不等同于 Servlet Filter。', '消息转换器负责对象与 HTTP body 的序列化/反序列化。', '统一异常处理应保留错误码、日志关联和敏感信息边界。'],
        mechanism: '前端控制器把不同 Controller 形式适配为统一调用流程，并通过可插拔组件完成路由、绑定、视图或响应体处理。',
    },
    {
        pattern: /\bb\+?树\b|索引|innodb|聚簇索引|回表|覆盖索引/,
        conclusion: 'InnoDB B+ 树索引用高扇出降低磁盘页访问：聚簇索引叶子保存整行，二级索引叶子保存主键；查询是否回表取决于所需列能否由二级索引覆盖。',
        facts: ['联合索引遵循有序前缀，范围条件后续列能否继续缩小扫描需结合版本与访问方式判断。', '页分裂、随机主键和过宽索引会增加写放大与空间成本。', 'EXPLAIN 要结合实际行数、过滤率、回表次数和执行时间验证，不能只看 type 字段。'],
        mechanism: '树的内部节点保存分隔键和子页指针，叶子按键有序并相连；一次查找沿根到叶定位页内记录，二级索引可能再以主键访问聚簇树。',
    },
    {
        pattern: /\bmvcc\b|readview|隔离级别|幻读|间隙锁|next-key/,
        conclusion: 'InnoDB MVCC 通过事务 ID、undo 版本链和 Read View 判断可见性；一致性读与当前读路径不同，RR 下当前读还会用 next-key lock 抑制范围幻影。',
        facts: ['RC 通常每次一致性读生成新 Read View，RR 通常在事务首次一致性读时建立并复用。', '快照读依据版本可见性，SELECT FOR UPDATE 和 DML 属于当前读并参与加锁。', '长事务会阻碍旧版本清理并增加 undo 压力。'],
        mechanism: '记录隐藏字段指向 undo 链，读取方按 Read View 的活跃事务边界沿版本链寻找可见版本；锁管理器处理当前读的记录与间隙冲突。',
    },
    {
        pattern: /redo log|undo log|binlog|两阶段提交|崩溃恢复/,
        conclusion: 'redo 保证 InnoDB 页修改可恢复，undo 支持回滚与多版本，binlog 记录 Server 层逻辑变更用于复制和归档；redo 与 binlog 通过内部两阶段提交保持提交一致。',
        facts: ['WAL 先让日志达到持久性要求，再允许脏页异步刷盘。', '典型提交链路包含 redo prepare、写 binlog、redo commit。', '恢复时依据 redo 状态与 binlog 完整性决定提交或回滚，具体细节需绑定 MySQL 版本。'],
        mechanism: '崩溃恢复先重放持久 redo 恢复页状态，再结合事务和 undo 清理未提交影响；复制端消费 binlog 重演已提交变更。',
    },
    {
        pattern: /\bzset\b|排行榜|跳表|skiplist/,
        conclusion: 'Redis ZSet 用哈希表定位 member、用跳表维护 score 有序关系，适合排行榜和范围查询；大榜单要按业务维度或时间窗口分片，并把全量精排与 TopN 召回分层。',
        facts: ['ZADD/ZINCRBY 更新分数，ZREVRANGE 或 ZRANGE REV 读取倒序名次，复杂度与成员数和返回数量相关。', '同分成员还会按 member 排序，业务若要求稳定并列名次需额外定义规则。', '亿级榜单不应让单个 ZSet 承担全部写热点，可按分区维护局部 TopN，再异步归并全局候选。'],
        mechanism: '哈希表提供 member 到 score 的 O(1) 期望定位，跳表按 score/member 有序并支持范围遍历；分片榜单通过局部增量更新和周期归并控制单 key 大小与热点。',
    },
    {
        pattern: /\blru\b|最近最少使用/,
        conclusion: 'LRU 要在 O(1) 内完成 get/put，经典结构是 HashMap 加双向链表：Map 定位节点，链表头尾表达最近使用顺序，访问或更新移到头部，超容量淘汰尾部。',
        facts: ['双向链表使已知节点删除和插入为 O(1)。', '使用虚拟头尾节点可消除空表和边界分支。', '并发 LRU 还要定义锁粒度、容量一致性和回调副作用，不能只给单线程代码。'],
        mechanism: '每次命中把节点从原位置摘下并插到头部；新增先写 Map 与链表，超过容量时删除尾前节点并同步移除 Map。',
    },
    {
        pattern: /布隆过滤器|bloom/,
        conclusion: '布隆过滤器用多个哈希函数把元素映射到位图，能确定“肯定不存在”或“可能存在”，适合在缓存/存储前挡住不存在请求，但不能单独给出无误判的存在性结论。',
        facts: ['位图越大、元素越少、哈希函数数量越合适，假阳性率越低。', '普通布隆过滤器删除位会影响其他元素；需要删除时考虑计数布隆过滤器。', '过滤器与权威数据更新不同步会产生业务风险，需设计重建、旁路和监控。'],
        mechanism: '写入时设置 k 个哈希位置，查询时只有 k 位全为 1 才判为可能存在；任一位为 0 即可确定未写入过。',
    },
    {
        pattern: /\baof\b|append only file/,
        conclusion: 'AOF 记录 Redis 写命令，恢复时重放日志；持久性由 appendfsync 策略决定，重写会生成等价但更紧凑的新文件，切换过程需保证增量不丢。',
        facts: ['always 延迟高但丢失窗口小，everysec 常在性能与持久性间折中，no 交给操作系统。', 'AOF 重写不是压缩旧字节，而是根据当前数据状态生成最小命令集合。', '恢复优先级、混合持久化和截断修复行为需绑定 Redis 版本与配置。'],
        mechanism: '主线程把写命令追加到 AOF 缓冲区，刷盘策略决定同步时机；后台重写期间的新写入进入增量缓冲，完成后原子替换文件。',
    },
    {
        pattern: /\brdb\b|bgsave|快照/,
        conclusion: 'RDB 是 Redis 某一时点的数据快照，文件紧凑且适合备份与快速加载；代价是两次快照之间可能丢数据，并且 fork 与写时复制会带来延迟和内存峰值。',
        facts: ['SAVE 阻塞主线程，BGSAVE 通常 fork 子进程生成快照。', '父子进程共享页，快照期间写入会触发 copy-on-write。', '生产评估要看数据量、脏页率、fork 延迟、内存余量和备份恢复目标。'],
        mechanism: 'fork 后子进程遍历快照时刻的内存视图写临时 RDB，完成后替换旧文件；父进程继续服务并通过页复制保持视图隔离。',
    },
    {
        pattern: /\bacid\b|事务.*(原子性|一致性|隔离性|持久性)|原子性.*持久性/,
        conclusion: 'ACID 分别描述事务的原子提交、一致性约束、并发隔离与提交持久性；数据库通过日志、锁/MVCC、约束和恢复共同实现，业务一致性仍需正确事务边界与不变量。',
        facts: ['原子性依赖回滚信息和提交协议，持久性依赖 redo/WAL 及刷盘策略。', '隔离级别是在并发异常与吞吐之间权衡，不等于绝对串行执行。', '一致性是应用与数据库约束共同维持的结果，数据库不会自动理解所有业务规则。'],
        mechanism: '事务执行期间记录 undo/redo 并参与并发控制，提交点把结果变为对其他事务可见且可恢复，回滚则沿 undo 撤销未提交影响。',
    },
    {
        pattern: /死锁|deadlock/,
        conclusion: '死锁是多个执行单元形成循环等待且条件无法自行解除；处理包括统一资源顺序、缩短持有时间、超时/检测回滚，并在数据库或线程快照中还原等待图。',
        facts: ['互斥、持有并等待、不可剥夺和循环等待是经典必要条件。', '数据库可检测等待图并选择代价较小事务回滚，应用仍需安全重试。', '减少锁范围有助于降低概率，但不能替代一致的加锁顺序。'],
        mechanism: '把线程/事务作为节点、等待关系作为有向边，出现环即存在死锁；解除通常要中止一个参与者释放资源。',
    },
    {
        pattern: /设计模式|单例模式|工厂模式|策略模式|观察者/,
        conclusion: '设计模式用于表达稳定的职责与变化点，不应为套模式而增加抽象；回答要从真实变化原因出发，说明参与者、调用关系、收益和新增复杂度。',
        facts: ['策略模式把可替换算法封装在统一接口后，由上下文组合使用。', '工厂隔离对象创建与使用，适合创建逻辑复杂或实现可替换的场景。', 'Java 线程安全单例优先考虑枚举或静态内部类；DCL 必须配合 volatile。'],
        mechanism: '模式通过组合、接口或受控创建把变化限制在局部；评估时比较直接实现的复杂度，确认抽象能消除真实重复或条件分支。',
    },
    {
        pattern: /equals|hashcode|==|integer.*缓存/,
        conclusion: 'Java 的 == 对基本类型比较值、对引用比较身份；equals 表达逻辑相等，重写 equals 时必须同步重写 hashCode，保证相等对象在哈希容器中得到相同哈希值。',
        facts: ['equals 需满足自反、对称、传递、一致和非空性。', 'hashCode 相同不代表 equals，哈希冲突由容器继续比较。', 'Integer 自动装箱可能命中缓存，不能用 == 判断包装值相等。'],
        mechanism: '哈希容器先按 hash 缩小桶范围，再用 equals 判断键；契约不一致会导致逻辑相等对象无法正确查找或删除。',
    },
    {
        pattern: /stringbuilder|stringbuffer|string.*不可变|字符串常量池/,
        conclusion: 'String 不可变便于共享、缓存哈希和安全发布；频繁拼接使用可变缓冲区，StringBuilder 无同步开销，StringBuffer 的方法级同步不等于复合操作天然正确。',
        facts: ['编译期常量拼接可能折叠，运行期循环拼接应避免反复创建中间 String。', 'String.intern 与字符串池行为需结合 JDK 版本和内存成本。', '不可变对象仍可能引用可变内部对象，真正不可变需防御性复制。'],
        mechanism: 'StringBuilder 维护可扩展字符/字节数组并追加，最终 toString 生成不可变结果；容量不足时重新分配和复制。',
    },
    {
        pattern: /mybatis|一级缓存|二级缓存|预编译参数/,
        conclusion: 'MyBatis 把 Mapper 调用映射为 SQL 执行、参数绑定、结果映射与插件链；井号参数使用预编译占位符，美元花括号是文本替换并有注入风险，只能用于严格白名单结构。',
        facts: ['一级缓存通常是 SqlSession 级，二级缓存是 namespace 级且需显式评估一致性。', '动态 SQL 应把值参数化，表名、排序列等结构只能从白名单生成。', '批量、分页和 N+1 查询需要结合实际驱动与 SQL 观察。'],
        mechanism: '代理 Mapper 生成 MappedStatement 调用 Executor，经 StatementHandler 参数化执行 JDBC，再由 ResultSetHandler 映射对象。',
    },
    {
        pattern: /进程.*线程|线程.*进程|协程/,
        conclusion: '进程是资源隔离与分配边界，线程是进程内调度执行单元，协程通常在用户态协作调度；选型取决于隔离、切换成本、阻塞模型和故障影响。',
        facts: ['同进程线程共享地址空间，通信方便但错误隔离较弱。', '线程切换涉及调度和寄存器/栈上下文，实际成本受工作集和锁竞争影响。', '协程遇到阻塞系统调用时需由运行时或异步 IO 避免阻塞整个执行线程。'],
        mechanism: '内核调度可运行线程，进程页表提供地址空间；协程运行时把多个逻辑任务复用到少量线程并保存用户态执行上下文。',
    },
    {
        pattern: /\bipc\b|进程间通信|共享内存|管道/,
        conclusion: 'IPC 选型要比较数据量、延迟、复制次数、同步方式和跨主机需求；管道/套接字传字节流，共享内存吞吐高但必须另做同步。',
        facts: ['匿名管道常用于亲缘进程，命名管道可让无亲缘本机进程通信。', '共享内存避免内核与用户间重复搬运，但并发一致性需信号量、锁或无锁协议。', 'Unix domain socket 适合本机双向通信，网络 socket 可跨主机。'],
        mechanism: '内核对象负责缓冲、唤醒和权限；共享内存把同一物理页映射到多个进程页表，由进程协作维护数据协议。',
    },
    {
        pattern: /虚拟内存|分页|缺页|page cache/,
        conclusion: '虚拟内存用页表把进程虚拟地址映射到物理页，提供隔离、按需分配和文件映射；性能分析要区分缺页、换页、page cache 与进程 RSS。',
        facts: ['TLB 缓存地址转换，命中率影响内存访问成本。', '缺页可能只是建立映射或从文件读取，不都意味着磁盘 swap。', 'mmap、sendfile 等技术通过页映射或内核传输减少用户态复制。'],
        mechanism: 'CPU 访问虚拟地址，经 TLB/页表翻译；映射缺失触发缺页异常，内核分配、载入或换入页面后恢复执行。',
    },
    {
        pattern: /\bspark\b|mapreduce|hadoop|hive|flink|数据倾斜/,
        conclusion: '大数据计算题应从数据分区、执行 DAG、shuffle、状态和容错解释；Spark 以阶段和内存计算优化批处理，Flink 以有状态流和 checkpoint 支持流式一致性，Hive 是 SQL 到执行计划的上层抽象。',
        facts: ['shuffle 会产生网络、序列化和落盘开销，是倾斜与长尾的常见来源。', '数据倾斜可通过预聚合、随机前缀、拆分热点 key 或广播小表缓解。', 'checkpoint 保存状态一致快照，语义还取决于 source/sink 是否参与可恢复协议。'],
        mechanism: '逻辑算子被优化并切成可调度任务，分区决定并行数据范围；失败时依据 lineage 或 checkpoint 重算/恢复状态。',
    },
    {
        pattern: /\brag\b|向量.*搜索|大模型|\bllm\b|transformer/,
        conclusion: 'RAG 把检索到的受控资料作为模型上下文，用于降低知识缺失和提供来源；质量取决于切分、召回、重排、上下文组织、生成约束与离线/在线评测。',
        facts: ['向量相似度擅长语义召回，但精确 ID、权限和时间过滤通常仍需结构化条件或混合检索。', '召回率、上下文相关性和最终答案正确率要分层评测。', '资料版本、权限、引用和无答案拒答是生产落地关键边界。'],
        mechanism: '文档切分并嵌入索引，查询生成向量召回候选，经重排和过滤后拼入提示，模型生成时保留来源与置信边界。',
    },
    {
        pattern: /链表|listnode/,
        conclusion: '链表题先画清节点与指针关系，再选择虚拟头、快慢指针、双指针或局部反转；每次改 next 前保存后继，并用空链表、单节点、头尾变更和环验证。',
        facts: ['虚拟头节点可统一删除首节点和普通节点。', '快慢指针可求中点、检测环和维持固定间距。', '原地反转的核心不变量是已反转前缀与未处理后缀边界清晰。'],
        mechanism: '算法通过有限指针重连改变可达关系；正确性依赖改写顺序不丢失后缀，并保证最终无意外环或断链。',
    },
    {
        pattern: /二叉树|\bbst\b|前序|中序|后序|层序|最近公共祖先/,
        conclusion: '树题先确定遍历顺序和递归函数语义：DFS 适合子树汇总与路径状态，BFS 适合层次和最短步数；BST 额外利用左小右大的有序性。',
        facts: ['递归函数要明确返回值代表高度、答案还是状态，避免依赖隐式全局变量。', '层序遍历用队列并在每层开始记录当前 size。', '递归深度最坏可到节点数，退化树需考虑显式栈或迭代方案。'],
        mechanism: '树的递归结构让父问题由左右子树结果组合；遍历中每个节点通常只处理一次，时间 O(n)，额外空间由树高或最大宽度决定。',
    },
    {
        pattern: /动态规划|\bdp\b|最长递增|最长公共|编辑距离|背包|股票|路径.*和/,
        conclusion: '动态规划的核心不是套表格，而是定义可复用子问题：写清状态含义、选择导致的转移、初始边界和计算顺序，再根据依赖压缩空间。',
        facts: ['状态必须包含做出后续决策所需的最小信息。', '无后效性意味着相同状态的未来只由当前状态决定。', '滚动数组前要确认转移不会读到本轮已覆盖值，并选择正确遍历方向。'],
        mechanism: 'DP 按拓扑顺序计算子问题并缓存结果，避免递归搜索重复展开；正确性可由最优子结构或计数划分证明。',
    },
    {
        pattern: /滑动窗口|双指针|最长.*子串|最短.*子数组/,
        conclusion: '滑动窗口适用于连续区间且约束能随边界单调维护的问题；右端扩张纳入元素，违反约束时移动左端恢复不变量，并在正确时机更新答案。',
        facts: ['窗口内要维护可 O(1) 或对数更新的计数、和、最大值等状态。', '含负数的区间和往往破坏普通滑窗的单调性，需考虑前缀和等方法。', '求最长与求最短的更新时机不同，应先用小样例验证。'],
        mechanism: '两个边界都只单向移动，每个元素至多进入和离开窗口一次，因此常把嵌套循环降为 O(n)。',
    },
    {
        pattern: /回溯|全排列|组合|子集|复原.*ip|岛屿/,
        conclusion: '回溯把候选空间组织成搜索树，按“选择—递归—撤销”遍历；剪枝必须证明被排除分支不可能产生合法答案，去重要区分同层选择与同一路径使用。',
        facts: ['先定义 path、start/index、剩余约束和结束条件。', '排序后同层跳过相同值是常见去重方式，不能误伤不同位置的合法选择。', '网格 DFS 要标记访问并明确是否需要恢复。'],
        mechanism: '深度优先展开一个部分解，约束失败立即返回，达到终止条件复制当前解；复杂度通常由搜索树规模决定。',
    },
    {
        pattern: /排序|快排|归并|堆排|top.?k|第\s*k\s*[大小]|最[大小]的\s*k/,
        conclusion: '排序与 TopK 题先根据是否需要全序、数据能否放内存、K 大小和稳定性选算法；全排序常为 O(n log n)，TopK 可用大小为 K 的堆或快速选择降低成本。',
        facts: ['快速排序平均 O(n log n)、最坏 O(n²)，随机化或三数取中可降低退化风险。', '归并排序稳定且时间 O(n log n)，但数组实现通常需 O(n) 辅助空间。', '求最大的 K 个通常维护小顶堆，堆顶是当前候选中最小者。'],
        mechanism: '比较排序通过分区、合并或堆有序性逐步确定元素位置；TopK 只维护答案边界，不必得到其余元素全序。',
    },
    {
        pattern: /\bsql\b|group by|join|窗口函数|查询.*学生|订单表/,
        conclusion: 'SQL 题先明确一行结果代表什么，再按过滤、关联、分组聚合、窗口计算和最终排序分层；复杂查询优先用 CTE 拆成可验证中间结果。',
        facts: ['WHERE 在分组前过滤行，HAVING 在聚合后过滤组。', 'JOIN 条件遗漏会产生笛卡尔积，外连接右表过滤放错位置会退化为内连接。', 'ROW_NUMBER、RANK、DENSE_RANK 对并列值处理不同，排序键还应保证确定性。'],
        mechanism: '逻辑执行顺序可按 FROM/JOIN、WHERE、GROUP BY、HAVING、SELECT/窗口、ORDER BY、LIMIT 理解；优化器可改写物理执行但不改变结果语义。',
    },
    {
        pattern: /redis|sentinel|缓存穿透|缓存击穿|缓存雪崩/,
        conclusion: 'Redis 题要区分单命令执行、数据结构、持久化、高可用和业务缓存治理；内存访问与事件驱动带来低延迟，但慢命令、大 key、热 key 和故障切换仍会放大尾延迟。',
        facts: ['RDB 是时点快照，AOF 记录写命令并可重写；持久性取决于刷盘策略。', '缓存穿透、击穿和雪崩分别侧重不存在数据、热点失效和大面积同时失效。', '分布式锁至少要有唯一持有者标识、原子释放、租约和业务幂等，不能只写 SETNX。'],
        mechanism: '事件循环用 IO 多路复用处理连接，命令操作内存数据结构；后台线程或子进程承担部分持久化与释放工作，集群通过槽位和复制分布数据。',
    },
    {
        pattern: /kafka|rocketmq|rabbitmq|消息队列|\bmq\b|消息积压/,
        conclusion: '消息系统设计要同时说明生产确认、持久化/复制、消费位点、重试、死信、幂等和积压治理；“不丢、不重、严格有序”不能脱离范围与成本承诺。',
        facts: ['at-least-once 常见且要求消费端幂等，exactly-once 只在明确边界和协议内成立。', '顺序性通常限定在同一分区或队列，扩大顺序范围会牺牲并行度。', '积压时先判断生产突增、消费变慢、分区不均或下游故障，再扩容和限流。'],
        mechanism: '生产者选择分区并等待确认，Broker 追加日志并复制，消费者拉取记录、处理副作用后提交位点；失败由重试主题、死信或补偿流程接管。',
    },
    {
        pattern: /\btcp\b|三次握手|四次挥手|time_wait|拥塞控制/,
        conclusion: 'TCP 提供面向连接的可靠字节流，依靠序号、确认、重传、滑动窗口和拥塞控制协作；三次握手同步双方收发能力，四次挥手允许双向独立关闭。',
        facts: ['TIME_WAIT 由主动关闭方常见持有，用于吸收旧报文并保证最后 ACK 可重传。', 'TCP 没有消息边界，应用协议必须自行定长、分隔或长度前缀解决粘包拆包。', '流量控制保护接收方，拥塞控制保护网络，二者不是一回事。'],
        mechanism: '发送方按序号维护未确认窗口，接收方累计或选择确认；超时与重复 ACK 驱动重传，拥塞窗口根据网络反馈变化。',
    },
    {
        pattern: /\bhttp\b|https|tls|浏览器|dns/,
        conclusion: 'HTTP 规定应用层请求响应语义，HTTPS 是 HTTP 运行在 TLS 上；完整链路应包含 DNS、连接建立、TLS 身份认证与密钥协商、HTTP 交换、缓存和连接复用。',
        facts: ['TLS 通常用非对称机制完成身份认证和密钥协商，再用对称密钥传输数据。', 'HTTP/2 在单连接上多路复用流，但 TCP 丢包仍可能影响同连接；HTTP/3 基于 QUIC。', 'GET/POST 的安全性和幂等性是语义约定，不能简单等同于是否加密。'],
        mechanism: '证书链把域名公钥绑定到受信 CA，握手协商密码套件并导出会话密钥，记录层随后提供机密性与完整性。',
    },
    {
        pattern: /epoll|io多路复用|\bnio\b|netty|零拷贝/,
        conclusion: 'IO 多路复用让一个线程等待多个描述符的就绪事件，epoll 通过兴趣集合和就绪队列避免每次线性扫描全部连接；它解决等待管理，不等于业务处理本身并行。',
        facts: ['LT 重复报告未处理完的就绪事件，ET 只在状态变化时通知并通常配合非阻塞循环读写。', '零拷贝是减少用户态复制和上下文切换的一组技术，不代表绝对零次复制。', 'Netty 还提供事件循环、缓冲区、编解码和背压，不能只概括为 epoll 封装。'],
        mechanism: '内核在描述符状态变化时把事件加入就绪结构，用户线程批量取得并处理；业务耗时任务需移出事件循环以免阻塞其他连接。',
    },
    {
        pattern: /分布式锁|redisson|redlock|setnx|zookeeper/,
        conclusion: '分布式锁用于跨进程互斥，但正确性取决于租约、持有者身份、原子释放、续期、故障模型和临界区幂等；需要强 fencing 时还应给资源操作携带单调令牌。',
        facts: ['Redis 常用 SET key value NX PX 建锁并用 Lua 校验 value 后删除。', '看门狗续期不能消除长暂停、网络分区和资源端旧持有者写入风险。', 'ZooKeeper 临时顺序节点可提供排队与会话失效语义，但仍需处理会话和业务副作用。'],
        mechanism: '锁服务把所有权编码为唯一 token 和有效期；客户端只在持有期执行临界区，资源端可比较 fencing token 拒绝过期持有者。',
    },
    {
        pattern: /分库分表|sharding|海量.*数据/,
        conclusion: '分库分表先从容量、吞吐和运维瓶颈出发，再设计稳定分片键、路由、扩容、全局 ID、跨分片查询和迁移方案；它是复杂度交换，不是默认优化手段。',
        facts: ['分片键要兼顾均匀性、主要查询路径和热点风险。', '跨分片 JOIN、分页、排序和事务都会引入聚合与一致性成本。', '扩容应有双写/回放/校验/切流/回滚闭环，不能一次性停机搬迁。'],
        mechanism: '路由层按分片函数定位物理节点，聚合层合并多分片结果；再均衡阶段复制存量并追平增量，最后切换权威路由。',
    },
    {
        pattern: /限流|令牌桶|漏桶|熔断|降级|高并发/,
        conclusion: '流量治理要先定义保护对象和过载信号，再组合限流、排队、熔断、降级与隔离；令牌桶允许受控突发，漏桶强调平滑输出，阈值必须由容量验证而非拍脑袋。',
        facts: ['限流位置可在接入层、服务、租户或资源维度，粒度决定公平性和成本。', '熔断依据失败/慢调用窗口阻止继续放大故障，半开阶段用小流量探测恢复。', '降级必须提前定义可牺牲功能、兜底数据和恢复条件。'],
        mechanism: '令牌按速率补充且桶有上限，请求取得令牌才放行；分布式实现需原子更新状态并处理时钟、热点和近似精度。',
    },
    {
        pattern: /幂等|最终一致性|分布式事务|\btcc\b|\bsaga\b|\b2pc\b/,
        conclusion: '跨服务一致性先定义业务不变量，再在强一致、最终一致和补偿成本间选择；幂等键、状态机、可靠事件、重试和对账是可恢复链路的基础。',
        facts: ['TCC 把业务显式拆为 Try/Confirm/Cancel，需处理空回滚、悬挂和重复调用。', 'Saga 通过一串本地事务与补偿适合长事务，但中间状态对外可见。', '消息最终一致性必须覆盖本地事务与事件原子性、重复消费、乱序和长期失败。'],
        mechanism: '状态机限制合法转换，事务内写业务与事件记录，后台可靠投递；消费端以业务幂等键提交副作用，对账任务发现并修复遗漏。',
    },
    {
        pattern: /elasticsearch|倒排索引|搜索引擎/,
        conclusion: 'Elasticsearch 以倒排索引服务全文检索，通过分词把词项映射到文档集合；写入先进入近实时索引链路，查询在分片执行后由协调节点合并结果。',
        facts: ['text 通常分词，keyword 保留整体值；映射设计错误会影响匹配、聚合和存储。', '深分页 from/size 成本高，稳定翻页可用 search_after 和一致排序键。', '分片数量、refresh、副本和段合并共同影响写入吞吐、查询延迟与恢复成本。'],
        mechanism: 'Lucene 段是不可变结构，新增和删除通过新段与删除标记表达，后台合并段；BM25 等相关性模型按词频和文档统计打分。',
    },
    {
        pattern: /docker|kubernetes|\bk8s\b|容器/,
        conclusion: '容器通过 namespace 隔离视图、cgroup 限制资源，并共享宿主机内核；Kubernetes 在期望状态与实际状态之间持续调谐，调度、探针、滚动发布和资源限制共同决定稳定性。',
        facts: ['镜像分层不等于运行时隔离，安全与资源边界仍依赖内核能力。', 'request 参与调度，limit 约束上限；CPU 限制可能节流，内存超限可能触发 OOMKill。', 'readiness 决定是否接流量，liveness 用于判断是否需要重启，二者不能混用。'],
        mechanism: '控制器观察 API 对象并不断调谐资源，调度器为 Pod 选节点，kubelet 驱动容器运行时达到声明状态。',
    },
    {
        pattern: /nacos|注册中心|配置中心|dubbo|\brpc\b/,
        conclusion: '服务治理题应说明服务注册/发现、健康检查、负载均衡、超时重试、配置推送和故障隔离；RPC 只是调用抽象，不能隐藏网络不可靠与重复执行。',
        facts: ['重试必须限定幂等调用并设置总超时预算，否则会放大故障。', '客户端缓存注册表能在控制面短暂故障时维持调用，但需处理陈旧实例。', '配置变更要校验、灰度、审计和回滚，动态不等于无风险。'],
        mechanism: '提供方注册实例和元数据，消费方订阅并本地路由；控制面推送变化，数据面按负载策略选择实例并执行序列化与网络传输。',
    },
    {
        pattern: /cpu.*100|内存泄漏|oom|jstack|jmap|arthas|慢.*sql|排查|故障/,
        conclusion: '生产排障遵循“确认影响—止血—按指标分层定位—最小实验验证—修复—复盘”，证据链要从监控和 trace 落到进程、线程、GC、SQL 或下游，而不是直接重启猜原因。',
        facts: ['CPU 高可用 top -H 定位线程，再把十进制线程号转十六进制关联 jstack。', '内存问题先区分堆、直接内存、Metaspace、线程和 page cache，再决定是否采集 dump。', '慢 SQL 要结合慢日志、执行计划、实际扫描行数、锁等待和数据库负载。'],
        mechanism: '先用时间线和关联 ID 缩小故障窗口，再用多份快照区分瞬态与持续状态；每个根因假设都应有可证伪的指标或实验。',
    },
];

const DOMAIN_DEFAULTS = {
    '数据库': ['先定义数据模型、访问路径和一致性要求。', '再解释存储/索引/事务内部链路。', '最后用执行计划、锁等待、日志和容量数据验证边界。'],
    'Java': ['先明确 JDK 版本与 API 语义。', '再讲核心数据结构、状态变化和并发边界。', '最后用复杂度、JMH 或诊断工具验证。'],
    'Java基础': ['先明确 JDK 版本与语言/运行时语义。', '再讲对象、内存、并发或容器内部机制。', '最后补充反例与可验证代码。'],
    '缓存': ['先定义命中、失效和一致性目标。', '再讲数据结构、更新链路和故障路径。', '最后检查热点、大 key、持久化与降级。'],
    '中间件': ['先说明组件解决的问题和交付语义。', '再走一遍生产、存储、消费或调用链路。', '最后覆盖重试、幂等、积压与可观测性。'],
    '系统设计': ['先量化用户量、QPS、数据量、延迟与一致性目标。', '再画核心读写链路和数据模型。', '最后覆盖过载、故障、降级、观测和容量演进。'],
    '计算机网络': ['先定位协议层和提供的语义。', '再按报文与状态机解释交互。', '最后讨论超时、重传、安全、连接复用和抓包验证。'],
    '操作系统': ['先定义资源和内核抽象。', '再解释调度、内存或 IO 状态变化。', '最后说明系统调用、指标与性能边界。'],
    '算法': ['先澄清输入输出、约束和边界。', '再定义不变量、状态或搜索空间。', '最后给出复杂度并用极端样例验证。'],
    '算法与数据结构': ['先澄清输入输出、约束和边界。', '再定义不变量、状态或搜索空间。', '最后给出复杂度并用极端样例验证。'],
    '其他': ['先把题目拆成定义、机制、边界和验证四部分。', '对不完整题干先向面试官确认输入输出和评价标准。', '只使用能由真实经历或可复现实验支持的结论。'],
};

function parseArgs(argv) {
    const options = { noWrite: false, overwrite: false, date: '2026-07-10' };
    for (let index = 2; index < argv.length; index++) {
        const arg = argv[index];
        if (arg === '--noWrite' || arg === '--check') options.noWrite = true;
        else if (arg === '--overwrite') options.overwrite = true;
        else if (arg === '--date') options.date = argv[++index];
        else if (arg === '--root') options.root = argv[++index];
    }
    return options;
}

function answerType(questions) {
    const values = questions.map((question) => question.question_type || '').join('|');
    if (/Coding|算法应用/.test(values)) return 'coding';
    if (/Behavioral|Non_Tech|Personal|Reflection/.test(values)) return 'behavior';
    if (/Project|Experience|PostMortem/.test(values)) return 'project';
    if (/Scenario|Architecture|Tooling|Integration|Analysis/.test(values)) return 'scenario';
    if (/UnderTheHood|LowLevel/.test(values)) return 'mechanism';
    return 'concept';
}

function selectPacks(record, questions) {
    const haystack = [
        record.canonical_title,
        ...(record.primary_entities || []),
        ...questions.flatMap((question) => question.tech_entities || []),
    ].join(' ').toLowerCase();
    return KNOWLEDGE_PACKS.filter((pack) => pack.pattern.test(haystack)).slice(0, 3);
}

function unique(values) {
    return [...new Set(values.filter(Boolean))];
}

function defaultFacts(record) {
    const domain = record.primary_domain?.l1 || '其他';
    return DOMAIN_DEFAULTS[domain] || DOMAIN_DEFAULTS['其他'];
}

function codingGuide(title) {
    const value = title.toLowerCase();
    const guide = {
        invariant: '先把输入输出、数据范围、是否允许修改输入和异常行为写成契约，再选择能被样例验证的不变量。',
        complexity: '目标复杂度由题目规模决定；实现后分别核算主循环、嵌套结构和辅助空间。',
        language: 'java',
        code: [
            'static final class ProblemSpec {',
            '    final String inputContract;',
            '    final String outputContract;',
            '    final int maxSize;',
            '    ProblemSpec(String in, String out, int n) {',
            '        this.inputContract = in;',
            '        this.outputContract = out;',
            '        this.maxSize = n;',
            '    }',
            '}',
        ],
    };
    if (/(^|：|\s)sql|select|查询.*(学生|订单|用户|部门)/.test(value)) {
        return {
            invariant: '先确定结果粒度和唯一键，再逐层验证关联行数、过滤位置、聚合口径和并列排序规则。',
            complexity: '执行成本取决于过滤后行数、连接算法、分组/排序规模和可用索引，应以实际执行计划验证。',
            language: 'sql',
            code: ['WITH base AS (', '    SELECT key_col, metric_col', '    FROM source_table', '    WHERE filter_col = :filter_value', '), ranked AS (', '    SELECT base.*,', '           ROW_NUMBER() OVER (PARTITION BY key_col ORDER BY metric_col DESC) AS rn', '    FROM base', ')', 'SELECT *', 'FROM ranked', 'WHERE rn = 1;'],
        };
    }
    if (/\blru\b|最近最少使用/.test(value)) {
        return {
            invariant: 'Map 与链表包含完全相同的节点；头部是最近访问，尾部是最久未访问，每次命中或更新都移到头部。',
            complexity: 'HashMap 定位与双向链表摘插均为 O(1)，总空间 O(capacity)。',
            language: 'java',
            code: ['final class LruCache {', '    static final class Node { int k, v; Node prev, next; Node(int k, int v) { this.k=k; this.v=v; } }', '    private final int cap; private final Map<Integer, Node> map = new HashMap<>();', '    private final Node head = new Node(0,0), tail = new Node(0,0);', '    LruCache(int cap) { this.cap=cap; head.next=tail; tail.prev=head; }', '    int get(int k) { Node n=map.get(k); if(n==null)return -1; moveFirst(n); return n.v; }', '    void put(int k,int v) { Node n=map.get(k); if(n!=null){n.v=v;moveFirst(n);return;}', '        n=new Node(k,v); map.put(k,n); addFirst(n);', '        if(map.size()>cap){Node old=tail.prev; unlink(old); map.remove(old.k);} }', '    private void moveFirst(Node n){unlink(n);addFirst(n);}', '    private void addFirst(Node n){n.next=head.next;n.prev=head;head.next.prev=n;head.next=n;}', '    private void unlink(Node n){n.prev.next=n.next;n.next.prev=n.prev;}', '}'],
        };
    }
    if (/合并区间|merge intervals/.test(value)) {
        return {
            invariant: '按起点排序后，已写入结果的区间互不重叠；当前区间只需与结果最后一个区间比较。',
            complexity: '排序 O(n log n)，线性合并 O(n)，结果之外额外空间取决于排序实现。',
            language: 'java',
            code: ['static int[][] mergeIntervals(int[][] a) {', '    if (a.length == 0) return a;', '    Arrays.sort(a, Comparator.comparingInt(x -> x[0]));', '    List<int[]> out = new ArrayList<>();', '    for (int[] cur : a) {', '        if (out.isEmpty() || out.get(out.size()-1)[1] < cur[0]) out.add(cur.clone());', '        else out.get(out.size()-1)[1] = Math.max(out.get(out.size()-1)[1], cur[1]);', '    }', '    return out.toArray(int[][]::new);', '}'],
        };
    }
    if (/合并\s*k\s*个.*链表|merge\s*k/.test(value)) {
        return {
            invariant: '小顶堆始终保存每条尚未耗尽链表的当前最小节点；弹出的节点是所有剩余节点中的全局最小值。',
            complexity: '总节点数 N、链表数 K 时，时间 O(N log K)，堆空间 O(K)。',
            language: 'java',
            code: ['static ListNode mergeK(ListNode[] lists) {', '    PriorityQueue<ListNode> pq = new PriorityQueue<>(Comparator.comparingInt(n -> n.val));', '    for (ListNode n : lists) if (n != null) pq.add(n);', '    ListNode dummy = new ListNode(), tail = dummy;', '    while (!pq.isEmpty()) { ListNode n = pq.remove(); tail.next = n; tail = n;', '        if (n.next != null) pq.add(n.next); }', '    return dummy.next;', '}'],
        };
    }
    if (/atoi|字符串转.*整数|string to integer/.test(value)) {
        return {
            invariant: '依次处理空白、符号和连续数字；累加前用上界反推判断溢出，停止于第一个非法字符。',
            complexity: '单次扫描 O(n)，额外空间 O(1)。',
            language: 'java',
            code: ['static int atoi(String s) {', '    int i=0, sign=1, value=0;', '    while(i<s.length() && s.charAt(i)==32)i++;', '    if(i<s.length() && (s.charAt(i)==43 || s.charAt(i)==45)) sign=s.charAt(i++)==45?-1:1;', '    while(i<s.length() && Character.isDigit(s.charAt(i))) {', '        int d=s.charAt(i++)-48;', '        if(value > (Integer.MAX_VALUE-d)/10) return sign>0?Integer.MAX_VALUE:Integer.MIN_VALUE;', '        value=value*10+d;', '    }', '    return sign*value;', '}'],
        };
    }
    if (/复原.*ip|分割成\s*ip/.test(value)) {
        return {
            invariant: '路径始终由合法的 0..255 段组成；剩余字符数必须能被剩余段数覆盖，四段且用完字符串时才收集。',
            complexity: 'IPv4 只有四段、每段最多三位，搜索分支有常数上界；输出空间由答案数量决定。',
            language: 'java',
            code: ['static List<String> restoreIp(String s) { List<String> out=new ArrayList<>(); dfsIp(s,0,new ArrayList<>(),out); return out; }', 'static void dfsIp(String s,int i,List<String> path,List<String> out){', '    if(path.size()==4){if(i==s.length())out.add(String.join(".",path));return;}', '    int remain=s.length()-i, slots=4-path.size(); if(remain<slots||remain>3*slots)return;', '    for(int len=1;len<=3&&i+len<=s.length();len++){', '        if(len>1&&s.charAt(i)==48)break; String part=s.substring(i,i+len);', '        if(Integer.parseInt(part)>255)break; path.add(part); dfsIp(s,i+len,path,out); path.remove(path.size()-1);', '    }', '}'],
        };
    }
    if (/接雨水|trapping rain/.test(value)) {
        return {
            invariant: '双指针维护左右已知最大高度；较低一侧的接水量只由该侧最大值决定，可以安全结算后移动。',
            complexity: '时间 O(n)，额外空间 O(1)。',
            language: 'java',
            code: ['static long trap(int[] h) {', '    int l=0,r=h.length-1,leftMax=0,rightMax=0; long ans=0;', '    while(l<r){', '        if(h[l]<=h[r]){leftMax=Math.max(leftMax,h[l]);ans+=leftMax-h[l++];}', '        else{rightMax=Math.max(rightMax,h[r]);ans+=rightMax-h[r--];}', '    }', '    return ans;', '}'],
        };
    }
    if (/岛屿/.test(value)) {
        return {
            invariant: '每发现一个未访问陆地就增加答案，并从该点淹没其整个四连通分量；每个格子最多访问一次。',
            complexity: 'm×n 网格时间 O(mn)，递归栈最坏 O(mn)。',
            language: 'java',
            code: ['static int islands(char[][] g){int ans=0;for(int i=0;i<g.length;i++)for(int j=0;j<g[0].length;j++)', '    if(g[i][j]==49){ans++;sink(g,i,j);}return ans;}', 'static void sink(char[][] g,int i,int j){', '    if(i<0||j<0||i==g.length||j==g[0].length||g[i][j]!=49)return;', '    g[i][j]=48;sink(g,i+1,j);sink(g,i-1,j);sink(g,i,j+1);sink(g,i,j-1);', '}'],
        };
    }
    if (/单例模式|singleton|双重.*锁|dcl/.test(value)) {
        return {
            invariant: '发布后所有线程看到同一个完全初始化实例；DCL 的第二次检查在锁内，volatile 禁止构造写入与引用发布发生危险重排。',
            complexity: '初始化后读取 O(1) 且不进入锁；空间 O(1)。',
            language: 'java',
            code: ['final class Singleton {', '    private Singleton() {}', '    private static volatile Singleton instance;', '    static Singleton getInstance() {', '        Singleton local = instance;', '        if (local == null) { synchronized (Singleton.class) {', '            local = instance; if (local == null) instance = local = new Singleton();', '        }}', '        return local;', '    }', '}'],
        };
    }
    if (/归并排序|merge sort/.test(value)) {
        return {
            invariant: '递归返回时左右半段分别有序，merge 每次取两段当前较小元素，写回后整个区间有序。',
            complexity: '时间 O(n log n)，数组辅助空间 O(n)，稳定。',
            language: 'java',
            code: ['static void mergeSort(int[] a,int l,int r,int[] tmp){', '    if(l>=r)return;int m=l+((r-l)>>>1);mergeSort(a,l,m,tmp);mergeSort(a,m+1,r,tmp);', '    int i=l,j=m+1,k=l;while(i<=m||j<=r)tmp[k++]=j>r||(i<=m&&a[i]<=a[j])?a[i++]:a[j++];', '    for(i=l;i<=r;i++)a[i]=tmp[i];', '}'],
        };
    }
    if (/最长递增.*子序列|\blis\b/.test(value)) {
        return {
            invariant: 'tails[len-1] 是长度为 len 的递增子序列所能取得的最小尾值；它不一定是实际答案序列，但长度正确。',
            complexity: '每个数二分替换，时间 O(n log n)，空间 O(n)。',
            language: 'java',
            code: ['static int lis(int[] a){', '    int[] tails=new int[a.length];int size=0;', '    for(int x:a){int l=0,r=size;while(l<r){int m=(l+r)>>>1;if(tails[m]<x)l=m+1;else r=m;}tails[l]=x;if(l==size)size++;}', '    return size;', '}'],
        };
    }
    if (/最长公共子序列|\blcs\b/.test(value)) {
        return {
            invariant: 'dp[i][j] 表示两个前缀的 LCS 长度；末字符相同则接在更短前缀答案后，否则舍弃一侧末字符取较大值。',
            complexity: '时间 O(mn)，完整表空间 O(mn)，只求长度可滚动到 O(min(m,n))。',
            language: 'java',
            code: ['static int lcs(String a,String b){', '    int[] dp=new int[b.length()+1];', '    for(int i=1;i<=a.length();i++){int diagonal=0;for(int j=1;j<=b.length();j++){', '        int old=dp[j];dp[j]=a.charAt(i-1)==b.charAt(j-1)?diagonal+1:Math.max(dp[j],dp[j-1]);diagonal=old;', '    }}return dp[b.length()];', '}'],
        };
    }
    if (/二叉树.*(深度|高度)|最大深度/.test(value)) {
        return {
            invariant: 'depth(node) 返回以 node 为根子树的最大层数，空节点为 0，非空节点为左右高度较大值加 1。',
            complexity: '每个节点一次，时间 O(n)，递归栈 O(h)。',
            language: 'java',
            code: ['static int depth(TreeNode node){', '    return node==null?0:1+Math.max(depth(node.left),depth(node.right));', '}'],
        };
    }
    if (/最近公共祖先|\blca\b/.test(value)) {
        return {
            invariant: '递归返回当前子树中找到的目标节点或其公共祖先；左右都非空时当前节点就是首次汇合点。',
            complexity: '普通二叉树时间 O(n)，递归栈 O(h)。',
            language: 'java',
            code: ['static TreeNode lca(TreeNode root,TreeNode p,TreeNode q){', '    if(root==null||root==p||root==q)return root;', '    TreeNode left=lca(root.left,p,q),right=lca(root.right,p,q);', '    return left!=null&&right!=null?root:(left!=null?left:right);', '}'],
        };
    }
    if (/回文.*(字符串|数)|验证回文/.test(value)) {
        return {
            invariant: '左右指针指向下一对待比较字符，按题意跳过非目标字符并统一大小写；任一对不等立即失败。',
            complexity: '时间 O(n)，额外空间 O(1)。',
            language: 'java',
            code: ['static boolean palindrome(String s){', '    int l=0,r=s.length()-1;while(l<r){', '        while(l<r&&!Character.isLetterOrDigit(s.charAt(l)))l++;', '        while(l<r&&!Character.isLetterOrDigit(s.charAt(r)))r--;', '        if(Character.toLowerCase(s.charAt(l++))!=Character.toLowerCase(s.charAt(r--)))return false;', '    }return true;', '}'],
        };
    }
    if (/第\s*k\s*[大小]|top.?k|最[大小]的\s*k/.test(value)) {
        return {
            invariant: '求最大的 K 个时，小顶堆只保留已扫描元素中的 K 大候选，堆顶是候选边界；新值更大才替换。',
            complexity: '时间 O(n log K)，堆空间 O(K)。',
            language: 'java',
            code: ['static int[] topK(int[] a,int k){', '    if(k<0||k>a.length)throw new IllegalArgumentException();', '    PriorityQueue<Integer> pq=new PriorityQueue<>();', '    for(int x:a){if(pq.size()<k)pq.add(x);else if(k>0&&x>pq.peek()){pq.remove();pq.add(x);}}', '    return pq.stream().mapToInt(Integer::intValue).toArray();', '}'],
        };
    }
    if (/反转.*链表|链表.*反转|reverse linked/.test(value)) {
        return {
            invariant: '遍历时 prev 始终是已反转前缀的头，cur 是尚未处理后缀的头；改写 cur.next 前必须保存 next。',
            complexity: '单次遍历 O(n)，迭代版额外空间 O(1)。',
            code: ['static ListNode reverse(ListNode head) {', '    ListNode prev = null, cur = head;', '    while (cur != null) {', '        ListNode next = cur.next;', '        cur.next = prev;', '        prev = cur;', '        cur = next;', '    }', '    return prev;', '}'],
        };
    }
    if (/删除.*倒数|倒数第.*节点/.test(value)) {
        return {
            invariant: '虚拟头节点避免删除首节点特判；fast 先走 n 步后，fast 与 slow 保持 n 个节点间距。',
            complexity: '一次遍历 O(n)，额外空间 O(1)。',
            code: ['static ListNode removeNthFromEnd(ListNode head, int n) {', '    ListNode dummy = new ListNode(0, head);', '    ListNode fast = dummy, slow = dummy;', '    for (int i = 0; i < n; i++) fast = fast.next;', '    while (fast.next != null) { fast = fast.next; slow = slow.next; }', '    slow.next = slow.next.next;', '    return dummy.next;', '}'],
        };
    }
    if (/合并.*(有序|排序).*(链表|数组)|merge.*list/.test(value)) {
        return {
            invariant: '结果尾指针 tail 之前始终有序，每次从两个当前候选中取较小者，最后接上未耗尽后缀。',
            complexity: '两个输入总长度为 n 时，时间 O(n)；复用节点时额外空间 O(1)。',
            code: ['static ListNode merge(ListNode a, ListNode b) {', '    ListNode dummy = new ListNode(), tail = dummy;', '    while (a != null && b != null) {', '        if (a.val <= b.val) { tail.next = a; a = a.next; }', '        else { tail.next = b; b = b.next; }', '        tail = tail.next;', '    }', '    tail.next = a != null ? a : b;', '    return dummy.next;', '}'],
        };
    }
    if (/链表.*环|环形链表|cycle/.test(value)) {
        return {
            invariant: '快指针每次两步、慢指针每次一步；有环必在环内相遇，相遇后一个指针回到头并同速前进会在入口相遇。',
            complexity: '时间 O(n)，额外空间 O(1)。',
            code: ['static ListNode detectCycle(ListNode head) {', '    ListNode slow = head, fast = head;', '    do {', '        if (fast == null || fast.next == null) return null;', '        slow = slow.next; fast = fast.next.next;', '    } while (slow != fast);', '    slow = head;', '    while (slow != fast) { slow = slow.next; fast = fast.next; }', '    return slow;', '}'],
        };
    }
    if (/两数之和/.test(value)) {
        return {
            invariant: '扫描到 nums[i] 时，哈希表只保存此前值到下标的映射；若 target-nums[i] 已存在，就得到两个不同下标。',
            complexity: '期望时间 O(n)，额外空间 O(n)。',
            code: ['static int[] twoSum(int[] nums, int target) {', '    Map<Integer, Integer> seen = new HashMap<>();', '    for (int i = 0; i < nums.length; i++) {', '        int need = target - nums[i];', '        if (seen.containsKey(need)) return new int[]{seen.get(need), i};', '        seen.put(nums[i], i);', '    }', '    return new int[0];', '}'],
        };
    }
    if (/三数之和|3sum/.test(value)) {
        return {
            invariant: '排序后固定 i，左右指针寻找 -nums[i]；跳过相同值保证结果不重复，并按三数和移动指针。',
            complexity: '排序加双指针，时间 O(n²)，除排序外额外空间 O(1)。',
            code: ['static List<List<Integer>> threeSum(int[] a) {', '    Arrays.sort(a); List<List<Integer>> ans = new ArrayList<>();', '    for (int i = 0; i < a.length - 2; i++) {', '        if (i > 0 && a[i] == a[i - 1]) continue;', '        int l = i + 1, r = a.length - 1;', '        while (l < r) {', '            long sum = (long) a[i] + a[l] + a[r];', '            if (sum < 0) l++; else if (sum > 0) r--;', '            else { ans.add(List.of(a[i], a[l], a[r]));', '                int x = a[l], y = a[r]; while (l < r && a[l] == x) l++; while (l < r && a[r] == y) r--; }', '        }', '    }', '    return ans;', '}'],
        };
    }
    if (/最长.*(无重复|不重复).*(子串|子数组)/.test(value)) {
        return {
            invariant: '窗口 [left,right] 内没有重复字符；记录字符最近位置，重复时 left 只能向右跳。',
            complexity: '每个位置至多进入和离开窗口一次，时间 O(n)，空间 O(字符集)。',
            code: ['static int longestUnique(String s) {', '    Map<Character, Integer> last = new HashMap<>();', '    int left = 0, ans = 0;', '    for (int right = 0; right < s.length(); right++) {', '        char c = s.charAt(right);', '        left = Math.max(left, last.getOrDefault(c, -1) + 1);', '        last.put(c, right); ans = Math.max(ans, right - left + 1);', '    }', '    return ans;', '}'],
        };
    }
    if (/最大子数组|连续子数组.*最大|maximum subarray/.test(value)) {
        return {
            invariant: 'bestEnding 表示必须以当前位置结尾的最大和，只可能从当前数重新开始或接在上一段之后。',
            complexity: '时间 O(n)，额外空间 O(1)。',
            code: ['static long maxSubArray(int[] a) {', '    if (a.length == 0) throw new IllegalArgumentException("empty");', '    long ending = a[0], best = a[0];', '    for (int i = 1; i < a.length; i++) {', '        ending = Math.max(a[i], ending + a[i]);', '        best = Math.max(best, ending);', '    }', '    return best;', '}'],
        };
    }
    if (/二分|binary search|旋转排序|峰值/.test(value)) {
        return {
            invariant: '循环中答案始终位于闭区间 [left,right]；每次用比较结果排除至少一半且不丢失候选。',
            complexity: '时间 O(log n)，额外空间 O(1)。',
            code: ['static int binarySearch(int[] a, int target) {', '    int left = 0, right = a.length - 1;', '    while (left <= right) {', '        int mid = left + ((right - left) >>> 1);', '        if (a[mid] == target) return mid;', '        if (a[mid] < target) left = mid + 1; else right = mid - 1;', '    }', '    return -1;', '}'],
        };
    }
    if (/层序|广度.*二叉树|bfs/.test(value)) {
        return {
            invariant: '队列中保存下一批待访问节点；每层开始时固定 size，循环 size 次即可保持层边界。',
            complexity: '每个节点入队出队一次，时间 O(n)，空间 O(树最大宽度)。',
            code: ['static List<List<Integer>> levelOrder(TreeNode root) {', '    List<List<Integer>> ans = new ArrayList<>();', '    if (root == null) return ans;', '    Queue<TreeNode> q = new ArrayDeque<>(); q.add(root);', '    while (!q.isEmpty()) {', '        int size = q.size(); List<Integer> level = new ArrayList<>();', '        while (size-- > 0) { TreeNode n = q.remove(); level.add(n.val);', '            if (n.left != null) q.add(n.left); if (n.right != null) q.add(n.right); }', '        ans.add(level);', '    }', '    return ans;', '}'],
        };
    }
    if (/快速排序|快排|quick sort/.test(value)) {
        return {
            invariant: '一次 partition 结束后基准落在最终位置，左侧不大于基准、右侧不小于基准，再递归处理两侧。',
            complexity: '平均 O(n log n)、最坏 O(n²)，递归栈平均 O(log n)；随机基准可降低退化概率。',
            code: ['static void quickSort(int[] a, int l, int r) {', '    if (l >= r) return;', '    int pivot = a[l + ((r - l) >>> 1)], i = l, j = r;', '    while (i <= j) {', '        while (a[i] < pivot) i++; while (a[j] > pivot) j--;', '        if (i <= j) { int t = a[i]; a[i++] = a[j]; a[j--] = t; }', '    }', '    quickSort(a, l, j); quickSort(a, i, r);', '}'],
        };
    }
    if (/括号.*合法|有效.*括号/.test(value)) {
        return {
            invariant: '栈只保存尚未匹配的左括号；遇到右括号时栈顶必须是对应类型，扫描结束栈必须为空。',
            complexity: '时间 O(n)，最坏额外空间 O(n)。',
            code: ['static boolean validBrackets(String s) {', '    Deque<Character> st = new ArrayDeque<>();', '    for (char c : s.toCharArray()) {', '        if (c == 40 || c == 91 || c == 123) st.push(c);', '        else if (c == 41 || c == 93 || c == 125) {', '            if (st.isEmpty()) return false;', '            char open = st.pop();', '            if ((c == 41 && open != 40) || (c == 93 && open != 91) || (c == 125 && open != 123)) return false;', '        }', '    }', '    return st.isEmpty();', '}'],
        };
    }
    if (/大数.*加|字符串.*加/.test(value)) {
        return {
            invariant: '从最低位向高位计算，carry 始终是上一位进位；某个输入耗尽后按 0 参与。',
            complexity: '时间 O(max(m,n))，结果空间 O(max(m,n))。',
            code: ['static String add(String a, String b) {', '    StringBuilder out = new StringBuilder();', '    int i = a.length() - 1, j = b.length() - 1, carry = 0;', '    while (i >= 0 || j >= 0 || carry != 0) {', '        int sum = carry + (i >= 0 ? a.charAt(i--) - 48 : 0) + (j >= 0 ? b.charAt(j--) - 48 : 0);', '        out.append(sum % 10); carry = sum / 10;', '    }', '    return out.reverse().toString();', '}'],
        };
    }
    if (/动态规划|\bdp\b|最长递增|编辑距离|背包|股票/.test(value)) {
        return {
            invariant: '先写清 dp 状态代表的子问题、转移只依赖已计算状态、初始化覆盖最小规模，最终答案对应明确状态。',
            complexity: '时间通常是状态数乘每个状态的转移数，空间由完整表或滚动依赖决定。',
            code: ['static long solveDp(int[] input) {', '    long[] dp = new long[input.length + 1];', '    // dp[i] 的业务含义、初值和转移必须按本题约束填写。', '    for (int i = 1; i <= input.length; i++) {', '        dp[i] = transition(dp, input, i);', '    }', '    return dp[input.length];', '}'],
        };
    }
    return guide;
}

function renderProjectAnswer(record, type, facts) {
    const title = record.canonical_title;
    const isBehavior = type === 'behavior';
    const frame = isBehavior ? 'STAR（情境、任务、行动、结果、反思）' : '背景—目标—职责—决策—结果—复盘';
    if (isBehavior && /自我介绍/.test(title)) {
        return {
            conclusion: '自我介绍不是复述简历，而是用“当前定位—两段匹配证据—岗位连接”在 60 至 90 秒内建立面试主线；所有公司、年限、项目和结果必须来自本人真实材料。',
            oneMinute: '第一句说明当前岗位方向和经验范围；中间用两项最匹配本岗位的能力，各配一个真实项目结果；最后说明本次求职关注点以及为何与目标岗位匹配。把技术栈作为证据嵌入项目，不连续报工具名。',
            threeMinute: '准备 60 秒和 90 秒两个版本。按现在、过去、未来组织：现在是职责与擅长领域；过去选两个能承接后续追问的真实案例，分别交代问题、本人行动和结果；未来说明想解决的问题与岗位连接。删除年龄、籍贯等无关信息，确保每句话都能承受细节追问。',
            details: unique(['当前定位与目标岗位匹配点', '两项可追问的真实项目证据', '明确个人职责和结果口径', ...facts]),
            mechanism: '自我介绍决定面试官最初的追问路径。信息越具体且与岗位越相关，越容易把后续讨论引到自己有证据的优势领域。',
            project: '填写模板：我目前负责[真实方向/职责]；过去[时间范围]主要积累了[能力一]和[能力二]。在[真实项目]中我负责[动作]，解决[问题]并得到[真实结果]。我希望下一阶段继续在[方向]深入，这与贵岗位的[要求]匹配。',
        };
    }
    if (isBehavior && /职业规划|未来.*规划/.test(title)) {
        return {
            conclusion: '职业规划要体现方向稳定、目标岗位匹配和可执行路径：近期胜任岗位并补齐能力，中期扩大问题与责任范围，长期方向保留弹性，避免只报职级或空泛管理目标。',
            oneMinute: '先说明未来两三年希望持续深耕的真实方向，再列出当前能力基础、下一步要补的技术/业务能力以及可执行行动；最后说明目标岗位能提供哪些问题场景，形成双向匹配。',
            threeMinute: '按近期、中期、长期展开。近期目标是完成岗位成功标准并在真实项目中补齐短板；中期目标是能独立负责更复杂链路、跨团队推动并沉淀方法；长期只描述希望创造的价值和能力形态，不承诺未经验证的具体职级。补充定期复盘和调整机制。',
            details: unique(['目标方向与过往证据一致', '行动包含项目、学习、反馈和复盘', '说明岗位为何能承接规划', ...facts]),
            mechanism: '面试官用职业规划判断稳定性、动机和岗位期望是否匹配。可信规划来自已有轨迹加下一步行动，而不是预测遥远职位。',
            project: '填写模板：我希望未来[时间范围]继续深耕[真实方向]。当前已有[证据]，下一步需要补齐[能力]，计划通过[真实行动]验证。贵岗位的[具体工作内容]与这条路径匹配；我会每[周期]用[结果指标/反馈]复盘调整。',
        };
    }
    if (isBehavior && /离职|为什么.*选择|选择.*公司|求职动机|换工作/.test(title)) {
        return {
            conclusion: '动机题用正向、具体、可验证的职业诉求回答：先客观说明变化原因，再讲下一阶段想解决的问题与目标岗位匹配，不贬低原团队，也不虚构目标公司信息。',
            oneMinute: '用一两句说明当前阶段已获得什么以及出现了什么客观变化；随后讲希望扩大哪类问题、能力或责任；最后用岗位职责、业务阶段或技术挑战中的具体信息解释匹配。',
            threeMinute: '完整回答包含感谢与收获、变化事实、个人目标、目标岗位连接和风险说明。对薪酬、地点等现实因素可以诚实但不过度展开；若存在空档或频繁变动，说明决策过程和避免重复发生的措施。',
            details: unique(['不泄露原公司敏感信息', '不用抱怨替代职业目标', '目标岗位信息只引用已确认事实', ...facts]),
            mechanism: '面试官关注离职原因是否会在新岗位重演，以及候选人是否做过理性选择。前后经历和目标的一致性比“标准答案”更重要。',
            project: '填写模板：我在当前/上一阶段获得了[真实收获]；这次变化主要因为[客观事实]。下一阶段我希望承担[问题/责任]，已通过[行动]准备。目标岗位的[已确认职责]与此匹配，所以做出选择。',
        };
    }
    if (isBehavior && /缺点|不足|优势|优点/.test(title)) {
        return {
            conclusion: '优势要有行为和结果证据，缺点要真实但不触碰岗位核心底线，并给出已执行的改进动作与变化；不要把“过于认真”包装成假缺点。',
            oneMinute: '选一个与岗位相关的优势，用具体案例说明如何产生结果；缺点选一个真实可改进项，说明触发场景、过去影响、采取的机制和当前变化，最后给出仍需观察的边界。',
            threeMinute: '优势按能力、行为、证据、适用边界表达；缺点按事实、根因、影响、行动、进展表达。准备追问所需的时间线和反馈来源，避免把性格标签当作结论。',
            details: unique(['优势证据可被具体追问', '缺点不是岗位不可接受风险', '改进行动已发生而非未来承诺', ...facts]),
            mechanism: '这类题校验自我认知与反馈闭环。能说明能力在何种条件下有效、缺点如何被机制化改进，比绝对化评价更可信。',
            project: '填写模板：我的优势是[具体能力]，在[真实场景]中我做了[动作]并得到[结果]。需要改进的是[真实不足]，它曾在[场景]造成[影响]；我从[时间]开始采用[机制]，目前通过[反馈/指标]看到[变化]。',
        };
    }
    if (isBehavior && /冲突|挑战|失败|挫折|压力|困难|错误/.test(title)) {
        return {
            conclusion: '冲突、挑战或失败题用真实 STAR 案例，重点不是渲染困难，而是说明你如何识别根因、做取舍、协调利益、承担责任并把教训转成后续机制。',
            oneMinute: '一句话交代情境和影响，明确你的任务；重点讲两三项个人行动及决策依据；给出真实结果，包括未完全解决的部分；最后说明复盘后新增的流程、工具或行为改变。',
            threeMinute: '先区分目标冲突、信息不对称、资源不足还是执行错误；说明你如何收集事实、与关键角色对齐、提出选项并承担决策。结果既讲业务/工程指标，也讲关系与后续影响。若自己有责任，直接承认并说明止损、修复和防复发。',
            details: unique(['STAR（情境、任务、行动、结果、反思）', '个人动作与团队动作分开', '失败案例包含止损和防复发', ...facts]),
            mechanism: '压力追问会检查时间线、动机和责任是否一致。真实案例能同时解释当时约束、行动选择和事后认知变化。',
            project: '填写模板：在[真实情境]下发生[冲突/失败]，影响是[事实]；我的责任是[边界]。我先[收集证据/止损]，再与[角色]对齐并选择[方案及理由]。结果为[真实结果]；之后新增[机制]，仍有[不足]。',
        };
    }
    return {
        conclusion: '这是一道需要真实个人证据的问题。复习时用' + frame + '组织一个具体案例，明确“我”负责什么、为什么这样决策、结果如何量化；仓库不替用户编造项目或职业经历。',
        oneMinute: '围绕「' + title + '」准备一个两分钟以内的真实案例：先用一句话交代背景和目标，再说明个人职责与最关键的两项行动，给出可核验结果，最后补一个不足和后续改进。没有真实数据时用范围或趋势表达，不虚构精确数字。',
        threeMinute: '完整回答按五步展开：一是背景和约束，避免大段项目介绍；二是你承担的任务及成功标准；三是列出候选方案和取舍；四是重点讲个人实际执行、协作冲突与风险控制；五是用上线指标、故障变化、效率或反馈证明结果，并说明如果重做会改变什么。追问时保持角色、时间线和数据前后一致。',
        details: unique([frame, ...facts, '准备失败或不足证据，而不只讲成功结果。', '团队成果与个人贡献分开表达。']),
        mechanism: '面试官通过具体追问校验经历真实性、决策能力和复盘深度。时间线、个人动作、取舍依据和结果证据互相印证，才能形成可信闭环。',
        project: '请把以下字段替换成自己的真实材料：背景[业务/规模/约束]；目标[成功标准]；职责[本人边界]；行动[关键决策及理由]；结果[指标/反馈]；复盘[不足与改进]。若没有对应经历，直接说明相邻经验和迁移思路。',
    };
}

function renderAnswer(record, questions, date) {
    const type = answerType(questions);
    const packs = selectPacks(record, questions);
    const facts = unique(packs.flatMap((pack) => pack.facts || []));
    const fallbackFacts = defaultFacts(record);
    const detailFacts = unique([...facts, ...fallbackFacts]).slice(0, 8);
    const entities = unique([...(record.primary_entities || []), ...questions.flatMap((question) => question.tech_entities || [])]).slice(0, 8);
    const sourceVariants = unique(questions.map((question) => question.original_question)).slice(0, 4);
    const followupSubject = record.canonical_title.replace(/[？?。！!]+$/, '');
    const metadata = {
        schema_version: 'answer.v1',
        canonical_id: record.canonical_id,
        version: 1,
        status: 'needs_update',
        updated_at: date,
        answer_type: type,
        quality_tier: 'long_tail_baseline',
        generator_version: GENERATOR_VERSION,
    };

    let conclusion = packs[0]?.conclusion || '复习「' + record.canonical_title + '」时，应先给直接结论，再按定义与目标、核心链路、关键边界、验证方式展开，避免只罗列名词。';
    let oneMinute = conclusion + ' 关键检查点包括：' + detailFacts.slice(0, 4).join('；') + '。';
    let threeMinute = '先界定题目中的概念、版本和约束，再按状态或数据流走一遍主链路；随后解释为什么采用该机制，并用失败路径、性能边界和替代方案校验结论。针对本题，应覆盖 ' + (entities.length ? entities.join('、') : record.primary_domain?.l2 || record.primary_domain?.l1 || '核心对象') + '，最后给出可观测指标或最小实验。';
    let mechanism = packs.length
        ? packs.map((pack) => pack.mechanism).join(' ')
        : '把入口条件、核心状态、状态转换和输出结果连成因果链；并发题补充原子性与可见性，存储题补充持久化与恢复，分布式题补充超时、重试、幂等和故障模型。';
    let project = '项目映射时选一个真实场景，记录规模、版本、约束、个人决策和验证指标。可以用日志、监控、压测、执行计划、线程/堆快照或故障演练证明结论；没有亲历时明确说“这是方案推演”，不要虚构生产结果。';

    if (type === 'project' || type === 'behavior') {
        const personal = renderProjectAnswer(record, type, detailFacts);
        conclusion = personal.conclusion;
        oneMinute = personal.oneMinute;
        threeMinute = personal.threeMinute;
        mechanism = personal.mechanism;
        project = personal.project;
    } else if (type === 'scenario') {
        conclusion = '这道场景题不能直接堆组件。先量化需求与容量，再给核心数据模型和读写链路，随后补一致性、幂等、过载保护、故障降级、可观测性和演进取舍。' + (packs[0] ? ' 核心技术判断：' + packs[0].conclusion : '');
        oneMinute = '围绕「' + record.canonical_title + '」先报假设：用户量、峰值 QPS、数据量、延迟和一致性目标；再画入口、服务、存储与异步链路，指出关键分区键或幂等键；最后说明限流、缓存、重试、降级、监控和容量验证。';
        threeMinute = '第一步澄清功能与非功能需求；第二步估算峰值容量和数据增长；第三步设计 API、数据模型及同步/异步主链路；第四步明确事务边界和失败恢复；第五步设计缓存、分片和热点治理；第六步给出 SLI、告警、压测与演练；最后讨论成本、复杂度和从单体到分布式的演进顺序。';
    }

    const details = unique([
        ...detailFacts,
        '题目原文中的范围与版本是假设边界，信息不足时先澄清。',
        '结论必须能由样例、日志、指标、源码或最小实验中的至少一种验证。',
    ]).slice(0, 10);
    const mistakes = [
        '只背名词或组件清单，没有把输入、状态变化和输出串起来。',
        '忽略版本、数据规模、并发度、一致性和失败模型，给出无条件结论。',
        type === 'project' || type === 'behavior'
            ? '把团队成果说成个人贡献，或编造精确指标和未亲历的生产细节。'
            : '只讲正常路径，不说明异常、降级、观测和替代方案。',
        type === 'coding'
            ? '没有先写不变量和边界样例，代码通过示例后也未核算复杂度。'
            : '用“看情况”结束回答，却没有列出决定选型的具体条件。',
    ];

    let codingSection = '';
    if (type === 'coding') {
        const coding = codingGuide(record.canonical_title);
        details.unshift('算法不变量：' + coding.invariant, '复杂度：' + coding.complexity);
        mechanism = '算法主线：' + coding.invariant + ' 每一步都要保持该不变量，结束条件使它推出目标结果。' + ' ' + coding.complexity;
        const language = coding.language || 'java';
        codingSection = '\n\n' + (language === 'sql' ? 'SQL 复习实现：' : 'Java 复习实现：') + '\n\n~~~' + language + '\n' + coding.code.join('\n') + '\n~~~';
    }

    const lines = [
        '<!-- xhs-answer: ' + JSON.stringify(metadata) + ' -->',
        '# ' + record.canonical_title,
        '',
        '> 长尾复习底稿：基于题干、题型、领域与实体规则生成；用于主动回忆和追问检查。涉及版本、个人经历或具体业务数据时，按题内边界与真实材料复核。',
        '',
        '## 核心结论',
        '',
        conclusion,
        '',
        '## 1 分钟版',
        '',
        oneMinute,
        '',
        '## 3 分钟版',
        '',
        threeMinute,
        '',
        '## 关键细节',
        '',
        ...details.map((item) => '- ' + item),
        '',
        '## 原理机制',
        '',
        mechanism + codingSection,
        '',
        '## 项目经验版',
        '',
        project,
        '',
        '## 常见追问',
        '',
        '- 问：' + followupSubject + '的核心判断是什么？答：' + conclusion,
        '- 问：这道题最先要澄清什么？答：先确认题目范围、运行版本、输入输出、数据规模、并发与一致性目标；这些条件会直接改变结论和选型。',
        '- 问：如何验证回答不是背诵？答：给出一个可复现样例或真实指标，沿入口、核心状态和输出走一遍，再用失败注入、边界数据或对照实验验证。',
        '- 问：方案的主要代价是什么？答：从复杂度、延迟、吞吐、内存/存储、可用性、一致性和运维成本逐项说明，并指出当前约束下接受该代价的原因。',
        '- 问：题目继续追问源码或底层时怎么答？答：先说明核心数据结构和状态转换，再定位关键入口、并发控制与异常路径；不确定的版本细节明确标注并回到源码或官方文档核验。',
        '',
        '## 易错点',
        '',
        ...mistakes.map((item) => '- ' + item),
        '',
        '### 复习定位',
        '',
        '- 领域：' + (record.primary_domain?.l1 || '其他') + ' / ' + (record.primary_domain?.l2 || '其他'),
        '- 关键实体：' + (entities.join('、') || '以题干为准'),
        '- 来源问法：' + sourceVariants.join('；'),
        '',
    ];
    return lines.join('\n');
}

function main(argv = process.argv) {
    const options = parseArgs(argv);
    const root = options.root ? path.resolve(options.root) : ROOT;
    const answersDir = path.join(root, 'review', 'answers');
    const canonicals = loadCanonicalQuestions({
        filePath: path.join(root, 'data', 'questions', 'canonical_questions.jsonl'),
    });
    const questions = loadQuestions({
        filePath: path.join(root, 'data', 'questions', 'questions.jsonl'),
    });
    const byCanonical = new Map();
    for (const question of questions) {
        if (!question.canonical_id) continue;
        if (!byCanonical.has(question.canonical_id)) byCanonical.set(question.canonical_id, []);
        byCanonical.get(question.canonical_id).push(question);
    }

    const generated = [];
    const drift = [];
    for (const record of canonicals) {
        const filePath = answerPath(record.canonical_id, { answersDir });
        const exists = fs.existsSync(filePath);
        if (exists) {
            const current = readAnswerFile(filePath);
            if (current.metadata.generator_version !== GENERATOR_VERSION) continue;
            if (!options.overwrite && !options.noWrite) continue;
        }
        const content = renderAnswer(record, byCanonical.get(record.canonical_id) || [], options.date);
        if (options.noWrite) {
            if (!exists || fs.readFileSync(filePath, 'utf8') !== content) {
                drift.push(path.relative(root, filePath));
            }
        } else {
            ensureDir(path.dirname(filePath));
            fs.writeFileSync(filePath, content, 'utf8');
            generated.push(path.relative(root, filePath));
        }
    }
    const report = {
        schema_version: 'long_tail_answer_generation.v1',
        ok: options.noWrite ? drift.length === 0 : true,
        generator_version: GENERATOR_VERSION,
        canonical_count: canonicals.length,
        generated_count: generated.length,
        drift_count: drift.length,
        drift: drift.slice(0, 100),
    };
    console.log(JSON.stringify(report, null, 2));
    return report.ok ? 0 : 1;
}

if (require.main === module) process.exitCode = main();

module.exports = { GENERATOR_VERSION, answerType, selectPacks, codingGuide, renderAnswer, main };
