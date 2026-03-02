#!/bin/bash

# 获取传入的 note id
NOTE_ID=$1

# 检查是否输入了 ID
if [ -z "$NOTE_ID" ]; then
    echo "使用方法: $0 <note_id>"
    exit 1
fi

# 定义路径变量
SOURCE_DIR="downloaded_images/${NOTE_ID}"
TARGET_DIR="note_img_txt"
TARGET_FILE="${TARGET_DIR}/${NOTE_ID}.txt"

# 1. 确保目标目录存在
mkdir -p "$TARGET_DIR"

# 2. 检查源目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "跳过：源目录 $SOURCE_DIR 不存在，停止操作。"
    exit 0
fi

# 3. 检查目标文件：如果已存在且大小 > 0 字节，则跳过
if [ -s "$TARGET_FILE" ]; then
    echo "跳过：有效的图片文本文件已存在 -> $TARGET_FILE"
    exit 0
fi

# 4. 检查源目录中是否有图片文件
IMAGE_COUNT=$(find "$SOURCE_DIR" -name "*.webp" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "跳过：源目录 $SOURCE_DIR 中没有找到图片文件。"
    exit 0
fi

# 5. 检查是否所有图片大小都为0
ZERO_SIZE_COUNT=0
for img in "$SOURCE_DIR"/*.{webp,jpg,jpeg,png}; do
    if [ -f "$img" ] && [ ! -s "$img" ]; then
        ZERO_SIZE_COUNT=$((ZERO_SIZE_COUNT + 1))
    fi
done 2>/dev/null

# 如果找到的文件中都是0大小，跳过
if [ "$ZERO_SIZE_COUNT" -eq "$IMAGE_COUNT" ] && [ "$IMAGE_COUNT" -gt 0 ]; then
    echo "跳过：所有图片文件大小都为0。"
    exit 0
fi

# 6. 调用模型识别图片中的文字
echo "正在调用 Gemini 2.5 Flash 处理 ID: $NOTE_ID 的图片..."

# 构建图片文件路径参数
# 使用 find 命令来处理 glob 扩展，并使用数组存储图片路径
mapfile -t IMAGES < <(find "$SOURCE_DIR" -type f \( -name "*.webp" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) -size +0c)

# 将图片路径数组转换为 gemini 命令参数格式
IMAGE_PARAMS=""
for img in "${IMAGES[@]}"; do
    IMAGE_PARAMS="$IMAGE_PARAMS @$img"
done

# 执行OCR识别并将结果写入目标文件
gemini --model gemini-2.5-flash -p "识别图片中的内容,识别成文字直接输出，不需要额外处理 $IMAGE_PARAMS" > "$TARGET_FILE"

# 7. 最终验证：检查刚刚生成的文件是否有效
if [ -s "$TARGET_FILE" ]; then
    echo "处理成功: $TARGET_FILE"
else
    # 如果生成的依然是空文件，将其删除以免误导后续判断
    rm -f "$TARGET_FILE"
    echo "处理失败：模型返回内容为空，已清理空文件。"
    exit 1
fi
