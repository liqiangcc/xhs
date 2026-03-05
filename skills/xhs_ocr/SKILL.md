---
name: xhs_ocr
description: 对小红书笔记图片执行 OCR，使用 AI 视觉能力直接识别图片文字，结果保存到 note_img_txt/。调用后 AI 自主循环处理直到完成指定批次。
---

# 小红书笔记图片 OCR (XHS OCR)

> **你就是 OCR 引擎**。使用 `view_file` 查看图片，用你的视觉能力识别文字，无需调用任何外部 OCR 工具或脚本。

## ⚠️ 关键规则

1. **禁止调用** `ai_parse_img_txt.sh`、`img_2_txt.sh`、`gemini` CLI 等外部脚本/工具。
2. **AI 自身即为 OCR**：通过 `view_file` 查看图片 → 识别文字 → `write_to_file` 保存结果。
3. **SafeToAutoRun = true**：所有 `run_command` 调用都设为自动执行。
4. **幂等安全**：已存在且 > 0 字节的 `note_img_txt/{id}.txt` 文件直接跳过。
5. **批量处理**：默认每批处理 10 个笔记，处理完一批后提交并继续下一批。

---

## 执行流程

### 步骤 A：获取待 OCR 笔记列表

执行（`SafeToAutoRun = true`）：
```bash
node scripts/find_ocr_needed.js --ids-only
```

输出每行一个笔记 ID。如果无输出，说明没有待处理笔记，直接结束。

取前 **10 个** ID 作为本批任务（或用户指定数量）。

---

### 步骤 B：逐个处理笔记

对每个笔记 ID，按以下顺序操作：

#### B1: 检查本地图片

使用 `list_dir` 检查 `downloaded_images/{id}/` 目录：

- **目录存在且有图片文件**（`.webp`、`.jpg`、`.png`）→ 进入 B3
- **目录不存在或为空** → 进入 B2

#### B2: 下载图片（仅在本地无图片时）

1. 使用 `view_file` 读取 `note_images/{id}_urls.txt`，获取图片 URL 列表
2. 对每个 URL，使用 `run_command` 下载到 `downloaded_images/{id}/` 目录：
   ```bash
   mkdir -p downloaded_images/{id}
   curl -sL -o downloaded_images/{id}/{序号}.webp "{url}"
   ```
   - 如果使用的是 Windows，使用 `New-Item -ItemType Directory -Force` 和 `Invoke-WebRequest`
3. 下载完成后进入 B3

#### B3: 使用 AI 视觉识别图片文字

1. **查看所有图片**：对 `downloaded_images/{id}/` 中的每个图片文件，使用 `view_file` 查看
   - 一次可以查看多张图片（并行调用 `view_file`）
   - 跳过大小为 0 的文件

2. **识别并提取文字**：
   - 忠实识别图片中的所有文字内容
   - 保持原始排版结构（标题、编号、换行）
   - 多张图片按顺序拼接，无需标注"第N张图"
   - **不要**添加任何额外解释、总结或格式化
   - **不要**翻译中文内容

3. **输出格式**：纯文本，直接是图片中的文字内容

#### B4: 保存 OCR 结果

使用 `write_to_file` 将识别结果写入 `note_img_txt/{id}.txt`：

```
write_to_file:
  TargetFile: note_img_txt/{id}.txt
  CodeContent: (识别出的文字内容)
```

- 如果所有图片都无法识别出有效文字（空白/纯装饰图），写入空文件并在控制台记录跳过原因
- **不要**设置 `IsArtifact = true`

---

### 步骤 C：批次完成后提交

1. 本批全部处理完成后，执行（`SafeToAutoRun = true`）：
   ```bash
   node scripts/commit_changes.js
   ```

2. **继续下一批**：回到步骤 A，重新执行 `find_ocr_needed.js --ids-only` 获取剩余任务。

3. **重复 A → B → C 循环**，直到步骤 A 无输出或已处理完用户指定数量。

---

## 示例

用户说：**"使用 xhs_ocr 处理笔记图片"**

AI 执行：
```
1. node scripts/find_ocr_needed.js --ids-only  → 获取 ID 列表
2. 对前 10 个 ID：
   a. list_dir downloaded_images/{id}/
   b. view_file downloaded_images/{id}/1.webp  (查看图片)
   c. view_file downloaded_images/{id}/2.webp  (查看图片)
   d. 识别文字：
      "美团二面 面试题
       1. HashMap 底层原理？
       2. ConcurrentHashMap 如何保证线程安全？
       ..."
   e. write_to_file note_img_txt/{id}.txt  (保存结果)
3. node scripts/commit_changes.js  → 提交
4. 回到步骤 1 继续下一批
```

---

## 注意事项

- 图片可能包含：面试题目列表、手写笔记、代码截图、表格等
- 对于代码截图，保留代码格式（缩进、换行）
- 对于表格，用文字还原表格结构
- 如果图片模糊无法识别，在对应位置标注 `[无法识别]`
- 每个笔记通常有 1-10 张图片
