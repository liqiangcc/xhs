#!/bin/bash

# 1. 基础参数检查
KEYWORD=${1:-"java社招面试"}
PAGE=${2:-1}
RAW_FILE="raw_curl.txt"

# 2. 检查模板是否存在
if [ ! -f "$RAW_FILE" ]; then
    echo "❌ 错误: 未找到模板文件 $RAW_FILE"
    echo "请先从浏览器复制搜索请求的 cURL 命令并保存为 $RAW_FILE"
    exit 1
fi

echo "--- 🔍 正在搜索: $KEYWORD (第 $PAGE 页) ---"

# 3. 动态替换参数
# 替换 keyword: "..." 为新的关键字
# 替换 page: ... 为新的页码
# 注意：使用 | 作为 sed 分隔符以处理关键字中可能存在的特殊字符
COMMAND=$(cat "$RAW_FILE" | \
    sed -E "s|\"keyword\":\"[^\"]*\"|\"keyword\":\"$KEYWORD\"|g" | \
    sed -E "s|\"page\":[0-9]+|\"page\":$PAGE|g")

# 4. 执行请求
# 使用 -s 保持静默，输出直接返回给调用者
eval "$COMMAND -s"