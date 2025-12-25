#!/bin/bash

# 加载环境变量
source ./config_env.sh

# 接收参数：$1 为关键词，$2 为页码
KEYWORD=${1:-"java社招面试"}
PAGE=${2:-1}

curl -s 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes' \
  -H 'accept: application/json, text/plain, */*' \
  -H "cookie: $XHS_COOKIE" \
  -H "user-agent: $XHS_UA" \
  -H "x-s: $XHS_XS" \
  -H "x-s-common: $XHS_S_COMMON" \
  -H "x-t: $XHS_XT" \
  -H 'content-type: application/json;charset=UTF-8' \
  -H 'origin: https://www.xiaohongshu.com' \
  -H 'referer: https://www.xiaohongshu.com/' \
  --data-raw '{
    "keyword": "'"$KEYWORD"'",
    "page": '"$PAGE"',
    "page_size": 20,
    "search_id": "2fqy04p0nlg530knl2qsa",
    "sort": "general",
    "note_type": 0,
    "ext_flags": [],
    "filters": [
      {"tags": ["general"], "type": "sort_type"},
      {"tags": ["不限"], "type": "filter_note_type"},
      {"tags": ["不限"], "type": "filter_note_time"},
      {"tags": ["不限"], "type": "filter_note_range"},
      {"tags": ["不限"], "type": "filter_pos_distance"}
    ],
    "geo": "",
    "image_formats": ["jpg", "webp", "avif"]
  }'
