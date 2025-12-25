#!/bin/bash

# 获取传入的 note id
NOTE_ID=$1

# 检查是否输入了 ID
if [ -z "$NOTE_ID" ]; then
    echo "使用方法: $0 <note_id>"
    exit 1
fi

# 定义路径变量
SOURCE_PATH="note_desc/${NOTE_ID}.txt"
TARGET_DIR="question"
TARGET_FILE="${TARGET_DIR}/${NOTE_ID}_desc_questions.txt"

# 1. 确保目标目录存在
mkdir -p "$TARGET_DIR"

# 2. 检查源文件：必须存在且内容不为空
if [ ! -s "$SOURCE_PATH" ]; then
    echo "跳过：源文件 $SOURCE_PATH 为空或不存在，停止操作。"
    exit 0
fi

# 3. 检查目标文件：如果已存在且大小 > 0 字节，则跳过
if [ -s "$TARGET_FILE" ]; then
    echo "跳过：有效的问题文件已存在 -> $TARGET_FILE"
    exit 0
fi

# 4. 调用模型：即使文件存在但大小为 0，也会走到这一步重新调用
echo "正在调用 Gemini 2.5 Flash 处理 ID: $NOTE_ID ..."

# 执行提取并将结果写入目标文件
# 注意：直接重定向会覆盖之前的 0 字节文件
gemini --model gemini-2.5-flash -p "@${SOURCE_PATH} 按顺序提取面试问题，需要给问题编号，直接输出结果，不要输出多余的内容" > "$TARGET_FILE"

# 5. 最终验证：检查刚刚生成的文件是否有效
if [ -s "$TARGET_FILE" ]; then
    echo "处理成功: $TARGET_FILE"
else
    # 如果生成的依然是空文件，将其删除以免误导后续判断
    rm -f "$TARGET_FILE"
    echo "处理失败：模型返回内容为空，已清理空文件。"
    exit 1
fi
