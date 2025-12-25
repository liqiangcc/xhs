#!/bin/bash

# 加载你之前 search 用的环境变量
source ./config_env.sh

NOTE_ID=$1
XSEC_TOKEN=$2

if [[ -z "$NOTE_ID" || -z "$XSEC_TOKEN" ]]; then
    echo "使用方法: bash get_detail.sh [ID] [TOKEN]"
    exit 1
fi

# 调用 feed 接口而非 explore 页面
curl -s 'https://edith.xiaohongshu.com/api/sns/web/v1/feed' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'content-type: application/json;charset=UTF-8' \
  -H "cookie: $XHS_COOKIE" \
  -H "user-agent: $XHS_UA" \
  -H "x-s: $XHS_XS" \
  -H "x-t: $XHS_XT" \
  --data-raw '{
    "source_note_id": "'"$NOTE_ID"'",
    "image_formats": ["jpg", "webp", "avif"],
    "extra": {"xsec_token": "'"$XSEC_TOKEN"'", "xsec_source": "pc_search"}
  }' | jq '.'
