# Skill: XHS Interview Note Pipeline (xhs_pipeline)

该技能用于驱动小红书面试笔记处理的全生命周期自动化，将原始笔记转化为高质量的结构化题库。

## 流程概览 (Execution Flow)

1. **[Discovery]** 运行 `node scripts/filter_notes.js` 获取当前待处理的高优先级笔记 ID 列表（推荐每批次 10 篇）。
2. **[Extraction]** 对每个 ID，调用 `xhs_extractor` 技能，通过 `note_desc` 和 `note_img_txt` 提炼面试题到 `note_structured/{id}.json`。
    - *注意*：若笔记内容为纯汇总或无效信息，questions 数组留空。
3. **[Hashing]** 对每个 ID，运行 `node scripts/xhs_process.js <id>`。此步骤将自动：
    - 验证结构化文件。
    - 调用 `generate_hashes.js` 为题目生成全局唯一 `question_id`。
4. **[Tagging]** 对每个 ID，调用 `xhs_tagger` 技能，根据题目内容进行多维度打标，输出到 `note_tagged/{id}.json`。
5. **[Persistence]** 一批次处理完成后，运行 `node scripts/commit_changes.js` 统一提交。

## 最佳实践 (Best Practices)

- **幂等性原则**：每个步骤都会自动检测已存在的文件。如果 `note_tagged/{id}.json` 已存在，应跳过该笔记。
- **批处理模式**：建议以 10个 ID 为一组进行循环，避免单次处理链路过长导致上下文过载。
- **错误处理**：如果某个 ID 在 Extraction 阶段被判定为无效，questions 设为空即可，后续 Hash 和 Tag 步骤会自动跳过。
- **性能监控**：处理完每批次后，运行 `node scripts/query_tagged.js stats` 查看当前题库总量和分布变化。

## 处理循环 (Processing Loop Template)

```bash
# 步骤 1: 获取 Candidate
node scripts/filter_notes.js

# 步骤 2-4: 针对每个 ID 循环 (由 Agent 内部逻辑驱动)
# [Loop Start]
# 调用 xhs_extractor -> 生成 note_structured
# 运行 node scripts/xhs_process.js <id> -> 生成 Hash
# 调用 xhs_tagger -> 生成 note_tagged
# [Loop End]

# 步骤 5: 归档
node scripts/commit_changes.js
```
