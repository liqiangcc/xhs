#!/bin/bash

# 配置目录
URL_DIR="note_images"
DOWNLOAD_ROOT="downloaded_images"

# 1. 检查 URL 目录是否存在
if [ ! -d "$URL_DIR" ]; then
    echo "错误: 找不到目录 $URL_DIR，请先运行提取脚本。"
    exit 1
fi

echo "开始批量检查并下载图片..."
echo "========================================"

# 2. 遍历 note_images 目录下的所有 URL 列表
for url_file in "$URL_DIR"/*_urls.txt; do
    [ -e "$url_file" ] || continue

    # 获取 Note ID
    note_id=$(basename "$url_file" _urls.txt)
    save_dir="${DOWNLOAD_ROOT}/${note_id}"
    
    # 创建该笔记的文件夹
    mkdir -p "$save_dir"

    echo "[笔记 $note_id]"

    # 3. 读取 URL 列表并下载
    count=1
    while IFS= read -r url; do
        [ -z "$url" ] && continue

        target_file="${save_dir}/${count}.webp"

        # --- 重复下载检查逻辑 ---
        if [ -f "$target_file" ] && [ -s "$target_file" ]; then
            # -f 检查是否存在, -s 检查文件大小是否大于0（防止下载到空文件）
            echo "  - 图片 $count: 已存在，跳过。"
        else
            echo "  - 图片 $count: 正在下载..."
            
            # 使用 curl 下载，带上超时和重试机制
            # --retry 3: 失败重试3次
            # --connect-timeout 5: 连接超时5秒
            curl -L -s --retry 3 --connect-timeout 5 -o "$target_file" "$url"
            
            # 检查下载是否成功
            if [ $? -eq 0 ]; then
                echo "    OK."
            else
                echo "    FAILED: $url"
                # 下载失败时删除可能产生的空文件，以便下次重试
                rm -f "$target_file"
            fi
        fi
        
        ((count++))
    done < "$url_file"

    echo "----------------------------------------"
done

echo "所有任务处理完成！"
