#!/bin/bash

# 1. 检查目标目录是否存在
JSON_DIR="note_json"
if [ ! -d "$JSON_DIR" ]; then
    echo "错误: 目录 $JSON_DIR 不存在。"
    exit 1
fi

# 2. 检查解析脚本是否存在
PARSE_SCRIPT="parse_image_urls.sh"
if [ ! -f "$PARSE_SCRIPT" ]; then
    echo "错误: 找不到脚本 $PARSE_SCRIPT"
    exit 1
fi

echo "开始批量遍历 $JSON_DIR 并提取图片链接..."
echo "------------------------------------------"

# 3. 循环遍历所有 json 文件
# 使用 count 记录处理数量
count=0

for file in "$JSON_DIR"/*.json; do
    # 确保文件确实存在（防止空目录时通配符失效）
    [ -e "$file" ] || continue
    
    # 提取 ID (去掉路径和 .json 后缀)
    note_id=$(basename "$file" .json)
    
    # 调用你的解析脚本
    # 使用 bash 显式调用，确保即使没有执行权限也能运行
    bash "$PARSE_SCRIPT" "$note_id"
    
    ((count++))
done

echo "------------------------------------------"
echo "处理完成！共处理了 $count 个文件。"
