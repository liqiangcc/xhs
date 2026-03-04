---
description: 全自动处理小红书面经笔记（筛选→提取→Hash→打标→提交），循环直到无剩余任务
---

// turbo-all

# XHS Pipeline 自动化流程

## 重要约束

- **唯一允许的脚本**：`node scripts/xhs_pipeline.js` 和 `node scripts/commit_changes.js`
- **禁止运行任何其他命令**：不允许 `ls`、`dir`、`Get-Item`、`head`、`cat`、`node scripts/generate_hashes.js` 等
- **文件检查**：使用 `find_by_name`、`list_dir`、`view_file` 等内置工具，**绝不使用 shell 命令**

## 步骤

1. 获取任务清单
```bash
node scripts/xhs_pipeline.js
```

2. 解析 JSON 输出，对每个 action 为 `extract_and_tag` 的任务：
   - 使用 `view_file` 工具读取 `desc_path` 和 `img_path`
   - 按 `xhs_extractor` skill 提取面试题
   - 使用 `write_to_file` 写入 `note_structured/{uuid}.json`
   - 获取 hash：
```bash
node scripts/xhs_pipeline.js hash {uuid}
```
   - 按 `xhs_tagger` skill 打标签
   - 使用 `write_to_file` 写入 `note_tagged/{uuid}.json`

3. 对每个 action 为 `tag_only` 的任务：
   - 直接用任务 JSON 中的 `hashes` 和 `metadata`
   - 按 `xhs_tagger` skill 打标签
   - 使用 `write_to_file` 写入 `note_tagged/{uuid}.json`

4. 本批全部完成后提交
```bash
node scripts/commit_changes.js
```

5. **立即回到步骤 1**，获取下一批任务。重复循环直到输出中 `summary.extract_and_tag == 0 && summary.tag_only == 0`。

6. 输出全量汇总报告。
