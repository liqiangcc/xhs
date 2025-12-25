#!/bin/bash

# 确保输出目录存在
mkdir -p note_desc

# 遍历 note_json 目录下所有的 .json 文件
for file in note_json/*.json; do
    # 检查文件是否存在（防止目录为空时报错）
    if [ -f "$file" ]; then
        # 提取文件名作为 ID（例如：从 note_json/abc.json 提取出 abc）
        note_id=$(basename "$file" .json)
        
        echo "正在处理: $note_id"
        
        # 调用你现有的脚本
        bash parse_desc.sh "$note_id"
    fi
done

echo "所有任务处理完成！"
