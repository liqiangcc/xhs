#!/bin/bash

# --- 配置 ---
SOURCE_DIR="note_desc"
PARSE_SCRIPT="./ai_parse_img_txt.sh"

# 定义带时间的打印函数
log_print() {
    # 格式: [2025-12-23 20:45:01] 内容
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 检查执行脚本是否存在
if [ ! -f "$PARSE_SCRIPT" ]; then
    log_print "错误: 找不到脚本 $PARSE_SCRIPT"
    exit 1
fi

# 获取文件总数
TOTAL_FILES=$(ls -1 "$SOURCE_DIR"/*.txt 2>/dev/null | wc -l)

if [ "$TOTAL_FILES" -eq 0 ]; then
    log_print "未在 $SOURCE_DIR 中发现 .txt 文件。"
    exit 0
fi

log_print "开始处理，总计文件数: $TOTAL_FILES"
echo "------------------------------------------"

CURRENT=0

for FILE_PATH in "$SOURCE_DIR"/*.txt; do
    [ -e "$FILE_PATH" ] || continue
    
    ((CURRENT++))
    NOTE_ID=$(basename "$FILE_PATH" .txt)
    PERCENT=$(( CURRENT * 100 / TOTAL_FILES ))
    
    # 打印进度和时间
    log_print "[${PERCENT}%%][${CURRENT}/${TOTAL_FILES}] 正在处理: ${NOTE_ID}"

    # 执行单个处理脚本
    # 注意：子脚本内部的 echo 也会直接显示出来，带上时间戳会更清晰
    bash "$PARSE_SCRIPT" "$NOTE_ID"
    
    # 检查返回状态，失败立即退出
    if [ $? -ne 0 ]; then
        echo "------------------------------------------"
        log_print "检测到故障 (ID: $NOTE_ID)，已停止任务。"
        exit 1
    fi
done

echo "------------------------------------------"
log_print "全部处理完成！"
