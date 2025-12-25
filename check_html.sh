#!/bin/bash

SOURCE_DIR="note_detail"
BAD_FILES_LIST="bad_files.txt"
> "$BAD_FILES_LIST"  # 清空旧的清单

echo "🔍 开始检查 $SOURCE_DIR 中的 HTML 文件..."

# 统计变量
TOTAL=0
BAD=0

# 遍历 HTML
for file in "$SOURCE_DIR"/*.html; do
    [ -e "$file" ] || continue
    ((TOTAL++))
    
    # 检查标准：如果不包含 INITIAL_STATE 或者包含了风控代码
    if grep -q "error_code=300013" "$file" || ! grep -q "window.__INITIAL_STATE__" "$file"; then
        echo "❌ 坏文件: $file"
        echo "$file" >> "$BAD_FILES_LIST"
        ((BAD++))
    fi
done

echo "------------------------------------------------"
echo "📊 检查完毕！"
echo "📦 总文件数: $TOTAL"
echo "⚠️  损坏文件: $BAD"

if [ $BAD -gt 0 ]; then
    echo "💡 建议处理：运行 'xargs rm < $BAD_FILES_LIST' 一键删除坏文件。"
else
    echo "✅ 恭喜！所有已下载文件均有效。"
fi
