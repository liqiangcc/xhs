---
description: 对小红书笔记图片执行OCR（AI视觉识别），结果保存到note_img_txt/，循环直到完成
---

// turbo-all

# XHS OCR 自动化流程

## 重要约束

- **职责单一**：不负责下载图片，不负责降级读取 desc，**只负责对本地已有的图片进行 OCR**。
- **禁止调用** `ai_parse_img_txt.sh`、`img_2_txt.sh`、`gemini` CLI。
- **AI 自身即为 OCR引擎**：通过 `view_file` 查看图片 → 识别文字 → `write_to_file` 保存。
- **文件检查**：使用 `list_dir`、`view_file` 等内置工具。
- **每轮只处理 1 条笔记**，处理完立刻提交再取下一条。

## 循环步骤

### 步骤 1：获取 1 条待 OCR 笔记 ID (仅限本地已有图片)

```bash
node scripts/find_ocr_needed.js --ids-only --limit 1 --local-images-only
```

- 如果**无输出**（空行），说明所有拥有本地图片的笔记均已完成 OCR 处理 → 跳到**步骤 5**
- 如果有输出，记录该 ID，继续步骤 2

### 步骤 2：读取本地图片并进行视觉 OCR

1. 使用 `list_dir` 检查 `downloaded_images/{id}/` 目录，获取里面的有效图片文件列表。
2. 使用 `view_file` 依次查看该目录下的每一张图片。
3. 识别每张图片中的**所有文字**，保持原始排版。多张图片之间用 `\n\n--- 图片 {n} ---\n\n` 分隔。
4. 使用 `write_to_file` 覆盖写入到 `note_img_txt/{id}.txt` 中。

### 步骤 3：提交

```bash
node scripts/commit_changes.js
```

### 步骤 4：继续循环

**立即回到步骤 1**，获取下一条具有本地图片的笔记。

### 步骤 5：完成

输出汇总报告，说明本次循环共完成了多少条本地图片的 OCR 任务。
