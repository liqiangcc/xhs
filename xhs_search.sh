#!/bin/bash
# 用法: ./xhs_search.sh "关键字" [数量]

# 引入配置
source ./config_env.sh 2>/dev/null || { echo "❌ 请先运行 refresh_config.sh"; exit 1; }

KEYWORD=${1:-$XHS_BIND_KW}
SIZE=${2:-20}
API_URL="https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"

echo "--- 🔍 发起搜索: $KEYWORD (Top $SIZE) ---"

# 1. 构造 Payload (修复了 invisible character 问题)
# 使用多行模式，清晰且不易出错
PAYLOAD=$(jq -nc \
  --arg kw "$KEYWORD" \
  --arg sz "$SIZE" \
  '{
    keyword: $kw, 
    page: 1, 
    page_size: ($sz|tonumber), 
    search_id: "2fqy04p0nlg530knl2qsa", 
    sort: "general", 
    note_type: 0, 
    ext_flags: [], 
    filters: [{tags: ["general"], type: "sort_type"}], 
    image_formats: ["jpg", "webp", "avif"]
  }')

# 2. 执行请求并解析
curl -s -X POST "$API_URL" \
  -H "content-type: application/json;charset=UTF-8" \
  -H "x-s: $XHS_XS" \
  -H "x-t: $XHS_XT" \
  -H "cookie: $XHS_COOKIE" \
  -H "user-agent: $XHS_UA" \
  -H "referer: https://www.xiaohongshu.com/" \
  --data-raw "$PAYLOAD"
