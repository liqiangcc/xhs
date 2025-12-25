#!/bin/bash

# 参数 $1 是 Note ID
if [ -z "$1" ]; then
    echo "用法: $0 <Note_ID>"
    echo "示例: $0 625564d70000000001025e46"
    exit 1
fi

NOTE_ID=$1
URL_FILE="note_images/${NOTE_ID}_urls.txt"
SAVE_DIR="downloaded_images/${NOTE_ID}"

# 1. 检查 TXT 列表是否存在
if [ ! -f "$URL_FILE" ]; then
    echo "错误: 找不到链接列表 $URL_FILE，请先运行脚本 1"
    exit 1
fi

mkdir -p "$SAVE_DIR"

# 2. 读取并下载
echo "开始下载笔记 $NOTE_ID 的图片..."
count=1
while IFS= read -r url; do
    [ -z "$url" ] && continue
    
    echo "下载第 $count 张..."
    # 使用双引号包裹 "$url" 解决 ! 符号报错问题
    curl -L -s -o "${SAVE_DIR}/${count}.webp" "$url"
    
    if [ $? -eq 0 ]; then
        ((count++))
    else
        echo "下载失败: $url"
    fi
done < "$URL_FILE"

echo "完成！图片保存在: $SAVE_DIR"
