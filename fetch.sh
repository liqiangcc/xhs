#!/bin/bash

# --- 配置区 ---
KEYWORD=$1
MAX_PAGE=20
dir=notes
mkdir -p $dir
OUTPUT_FILE="$dir/$1.txt"
# 清空旧结果
> "$OUTPUT_FILE"

echo "🚀 开始自动化抓取任务：$KEYWORD (共 $MAX_PAGE 页)"
echo "------------------------------------------------"
printf "%-25s | %-50s | %s\n" "ID" "XSEC_TOKEN" "TITLE"

# --- 逻辑区 ---
for (( p=1; p<=$MAX_PAGE; p++ ))
do
    echo "--- 正在抓取第 $p 页 ---"
    
    # 调用 search.sh 并获取原始 JSON
    raw_json=$(bash search.sh "$KEYWORD" "$p")

    # 检查返回是否包含错误 (例如 {"code":-1, "msg": "签名失效"})
    is_success=$(echo "$raw_json" | jq -r '.success // false')
    if [ "$is_success" != "true" ]; then
        echo "❌ 警告：第 $p 页请求失败。原因：$(echo "$raw_json" | jq -r '.msg // "未知错误"')"
        echo "可能是 x-s 签名过期或与 page 参数不匹配。"
        break
    fi

    # 提取字段：id, token, title
    # 注意：使用 jq 的 ? 运算符防止字段缺失导致报错
    extracted_data=$(echo "$raw_json" | jq -r '.data.items[]? | select(.model_type=="note") | "\(.id) | \(.xsec_token // .note_card.user.xsec_token) | \(.note_card.display_title)"')

    if [ -z "$extracted_data" ]; then
        echo "ℹ️ 第 $p 页没有更多笔记了。"
        break
    fi

    # 打印到控制台并追加到文件
    echo "$extracted_data"
    echo "$extracted_data" >> "$OUTPUT_FILE"

    # 检查是否还有更多页 (has_more)
    has_more=$(echo "$raw_json" | jq -r '.data.has_more // false')
    if [ "$has_more" != "true" ]; then
        echo "🏁 已到达最后一页。"
        break
    fi

    # 身体第一，遵循 3 秒原则
    if [ $p -lt $MAX_PAGE ]; then
        echo "⏳ 休息 3 秒以保护账号..."
        sleep 3
    fi
done

echo "------------------------------------------------"
echo "✅ 任务完成！共有数据保存至：$OUTPUT_FILE"
