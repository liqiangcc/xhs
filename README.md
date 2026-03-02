# 📚 小红书面经采集工具链

从小红书搜索、抓取面试经验笔记，通过 AI 自动提取面试题目，构建结构化面试题库。

## 架构

```
搜索 → 抓取列表 → 下载详情 → 解析JSON → 提取正文/图片 → AI提取面试题
```

```
search.sh                     # 单次搜索API调用
  └── fetch.sh                # 分页批量搜索，输出笔记ID列表
        └── fetch_detail.sh   # 批量抓取笔记HTML（带限速+熔断）
              └── html_to_json.sh + detail_to_json.py  # HTML → JSON
                    ├── json_2_desc_txt.sh → parse_desc.sh        # 提取正文
                    ├── json_2_img_urls.sh → parse_image_urls.sh  # 提取图片URL
                    │     └── url_2_img.sh / download_images.sh   # 下载图片
                    ├── desc_2_questions.sh → ai_parse_desc_2_question.sh  # AI提取面试题
                    └── img_2_txt.sh → ai_parse_img_txt.sh                # AI OCR图片
```

## 依赖

- `bash`, `curl`, `jq`, `python3`
- `gemini` CLI（用于 AI 提取面试题和图片 OCR）

## 快速开始

### 1. 准备凭证

从浏览器开发者工具中复制小红书搜索请求的 cURL 命令，保存为 `raw_curl.txt`。

笔记详情请求的 cURL 命令保存为 `raw_curl_detail.txt`。

### 2. 搜索笔记

```bash
# 搜索关键字，自动翻页（最多20页），结果存入 notes/ 目录
bash fetch.sh "java社招面试"
```

### 3. 抓取笔记详情

```bash
# 批量抓取所有搜索到的笔记HTML，存入 note_detail/
# 自动跳过已下载、随机限速、每20次休息5分钟
bash fetch_detail.sh
```

### 4. 解析数据

```bash
# HTML → JSON
bash html_to_json.sh

# JSON → 正文文本
bash json_2_desc_txt.sh

# JSON → 图片URL → 下载图片
bash json_2_img_urls.sh
bash url_2_img.sh
```

### 5. AI 提取面试题

```bash
# 从正文中提取面试题（需要 gemini CLI）
bash desc_2_questions.sh

# 从图片中 OCR 提取文字
bash img_2_txt.sh
```

### 6. 数据质量检查

```bash
# 检查损坏的HTML文件（风控拦截等）
bash check_html.sh
```

## 目录结构

```
notes/              # 搜索结果（ID + token 列表）
note_detail/        # 原始HTML页面
note_json/          # 提取的结构化JSON
note_desc/          # 笔记正文文本
note_images/        # 图片URL列表
downloaded_images/  # 已下载的图片
question/           # AI提取的面试题
note_img_txt/       # AI OCR识别结果
```

## 设计特点

- **断点续传** — 所有脚本检测已处理文件，自动跳过
- **反爬保护** — 随机延迟 + 批次休息 + 错误熔断
- **数据校验** — `check_html.sh` 检测损坏文件
- **幂等执行** — 重复运行不会产生重复数据
