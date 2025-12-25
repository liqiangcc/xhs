#!/bin/bash

# --- 配置区 ---
NOTES_DIR="notes"
SAVE_DIR="note_detail"
TASK_LIST="unique_tasks.tmp"
DETAIL_EXEC="./detail"
LOG_FILE="fetch.log"

# --- 日志函数 ---
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 1. 环境准备
mkdir -p "$SAVE_DIR"
echo "--- 任务开启时间: $(date) ---" >> "$LOG_FILE"

# 2. 预处理去重
log "🔍 正在扫描 $NOTES_DIR 并去重..."
cat "$NOTES_DIR"/*.txt 2>/dev/null | awk -F'|' '{print $1"|"$2}' | sort -u > "$TASK_LIST"

TOTAL=$(wc -l < "$TASK_LIST")
if [ "$TOTAL" -eq 0 ]; then
    log "⚠️ 未发现任务，请检查 $NOTES_DIR"
    exit 0
fi
log "📦 共有 $TOTAL 个唯一笔记待处理。"

# 3. 自动化循环执行
COUNT=0
BATCH_COUNT=0  # 新增：用于记录当前批次的请求数

while IFS='|' read -r note_id token; do
    ((COUNT++))
    note_id=$(echo "$note_id" | xargs)
    token=$(echo "$token" | xargs)

    if [[ -n "$note_id" && -n "$token" ]]; then
        # 3a. 跳过已存在
        if [ -f "$SAVE_DIR/${note_id}.html" ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - [$COUNT/$TOTAL] ⏭️ 跳过: $note_id" >> "$LOG_FILE"
            continue
        fi

        # 3b. 执行抓取
        log "📡 [$COUNT/$TOTAL] 正在请求 ID: $note_id ..."
        DETAIL_OUT=$(bash "$DETAIL_EXEC" "$note_id" "$token" 2>&1)
        EXIT_CODE=$?

        # 3c. 结果处理
        if [ $EXIT_CODE -ne 0 ]; then
            log "❌ 失败：$note_id。详情: $DETAIL_OUT"
            log "🛑 触发熔断，脚本停止。"
            rm -f "$TASK_LIST"
            exit 1
        else
            log "✅ 成功保存: $note_id"
            ((BATCH_COUNT++)) # 只有真正执行成功的请求才计入批次
        fi
        
        # --- 核心修改：每 20 次请求休息 5 分钟 ---
        if [ "$BATCH_COUNT" -ge 20 ]; then
            log "☕ 已完成 20 次请求，触发深度休息：5 分钟..."
            sleep 300
            BATCH_COUNT=0 # 重置批次计数
        else
            # 3d. 原有频率保护：随机 10-20 秒
            WAIT=$((RANDOM % 11 + 10))
            log "😴 频率保护，随机等待 ${WAIT}s..."
            sleep $WAIT
        fi
    fi
done < "$TASK_LIST"

# 4. 清理
rm -f "$TASK_LIST"
log "🎉 任务处理完毕。"
