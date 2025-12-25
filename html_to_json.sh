#!/bin/bash

# --- 配置 ---
SOURCE_DIR="note_detail"
LOG_FILE="extract.log"
PYTHON_EXEC="python3 detail_to_json.py"

# 初始化计数器
SUCCESS_COUNT=0
FAILED_COUNT=0

# 1. 检查环境
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ 错误: 找不到源目录 $SOURCE_DIR"
    exit 1
fi

echo "🚀 开始批量提取任务 (源目录: $SOURCE_DIR)"
echo "--- 提取任务启动: $(date) ---" > "$LOG_FILE"

# 2. 遍历 HTML 文件
# 使用 find 配合 while 循环，处理文件名包含空格的情况（更稳健）
find "$SOURCE_DIR" -name "*.html" | while read -r html_file; do
    
    # 调用 Python 脚本处理
    $PYTHON_EXEC "$html_file" >> "$LOG_FILE" 2>&1
    
    # 3. 检查返回值 (你要求的 -1 逻辑)
    if [ $? -eq 0 ]; then
        ((SUCCESS_COUNT++))
        # 在终端显示简要进度
        echo -n "✅" 
    else
        ((FAILED_COUNT++))
        echo -n "❌"
        # 将失败的文件记录到专门的错误清单，方便你醒来重抓
        echo "$html_file" >> "failed_list.txt"
    fi

    # 每处理 50 个文件换一行，方便观察
    if [ $(( (SUCCESS_COUNT + FAILED_COUNT) % 50 )) -eq 0 ]; then
        echo " ($((SUCCESS_COUNT + FAILED_COUNT)) processed)"
    fi
done

# 4. 汇总结果
echo -e "\n\n------------------------------------------------"
echo "📊 任务完成！"
echo "✅ 成功提取: $SUCCESS_COUNT"
echo "❌ 失败数量: $FAILED_COUNT"
echo "📝 详细日志见: $LOG_FILE"
[ -f "failed_list.txt" ] && echo "⚠️  失败列表已存入: failed_list.txt (可尝试删除这些 HTML 后重抓)"
echo "------------------------------------------------"
