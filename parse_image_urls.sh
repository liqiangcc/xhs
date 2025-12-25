#!/bin/bash

# 1. 检查输入
if [ -z "$1" ]; then
    echo "用法: $0 <Note_ID>"
    exit 1
fi

NOTE_ID=$1
JSON_FILE="note_json/${NOTE_ID}.json"
OUTPUT_DIR="note_images"
OUTPUT_FILE="${OUTPUT_DIR}/${NOTE_ID}_urls.txt"

# 2. 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 3. 检查 JSON 文件
if [ ! -f "$JSON_FILE" ]; then
    echo "错误: 找不到文件 $JSON_FILE"
    exit 1
fi

# 4. 使用 jq 提取图片链接
# 我们提取 urlDefault，这是默认的高清图链接
# 如果你想提取所有尺寸，可以修改路径为 .infoList[].url
echo "正在提取笔记 $NOTE_ID 的图片链接..."

jq -r ".note.noteDetailMap[\"$NOTE_ID\"].note.imageList[].urlDefault" "$JSON_FILE" > "$OUTPUT_FILE"

# 5. 结果反馈
if [ -s "$OUTPUT_FILE" ]; then
    echo "成功！图片链接已保存至: $OUTPUT_FILE"
    echo "链接预览："
    cat "$OUTPUT_FILE"
else
    echo "未发现图片链接或提取失败。"
    rm -f "$OUTPUT_FILE"
fi
