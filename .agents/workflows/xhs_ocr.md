---
description: 对小红书笔记图片执行OCR（AI视觉识别），结果保存到note_img_txt/，循环直到完成
---

// turbo-all

# XHS OCR 自动化流程

## 重要约束

- **禁止调用** `ai_parse_img_txt.sh`、`img_2_txt.sh`、`gemini` CLI
- **AI 自身即为 OCR**：通过 `view_file` 查看图片 → 识别文字 → `write_to_file` 保存
- **文件检查**：使用 `list_dir`、`view_file` 等内置工具

## 步骤

1. 获取待 OCR 笔记 ID 列表
```bash
node scripts/find_ocr_needed.js --ids-only
```

2. 取前 10 个 ID，对每个 ID：
   - 使用 `list_dir` 检查 `downloaded_images/{id}/` 是否有图片
   - 如无图片，读取 `note_images/{id}_urls.txt` 获取 URL 并下载
   - 使用 `view_file` 查看所有图片文件（支持 .webp/.jpg/.png）
   - 识别图片中的所有文字，保持原始排版
   - 使用 `write_to_file` 写入 `note_img_txt/{id}.txt`

3. 本批全部完成后提交
```bash
node scripts/commit_changes.js
```

4. **立即回到步骤 1**，获取下一批。重复循环直到 `find_ocr_needed.js` 无输出。

5. 输出汇总报告。
