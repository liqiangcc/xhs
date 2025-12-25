#!/bin/bash

ID=$1
TOKEN=$2
MODE=$3

if [[ -z "$ID" || -z "$TOKEN" ]]; then
    echo "用法: ./xhs_detail.sh <ID> <TOKEN> [-s]"
    exit 1
fi

# 获取页面
curl "https://www.xiaohongshu.com/explore/${ID}?xsec_token=${TOKEN}&xsec_source=pc_search&source=unknown" \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8' \
  -b 'abRequestId=97351e55-3b4e-5493-9f0f-a05a7b2a9bd4; xsecappid=xhs-pc-web; a1=196e118b2a7jloxm11z3lt2jkb5b16ptzm5cvtlyd50000384276; webId=60cd45f186f7a9998fb53f7b715bff2d; gid=yjKdyyYSS8ujyjKdyyYDJ6910WV1lC6yyuq12vf9JVTD2S28DyKU9h888qY4JWK824K0fjSK; webBuild=5.1.1; web_session=040069b128200656cdf4748e723b4bf299087a; id_token=VjEAALer9ad055x5Lxm5sl1P5WSlL3nBKPCKyE7DhQRJmDSu16/j3bM9faUISN9kiBaH2FRKbcxbyMhyctq2UO4XZy7rOxwldr5kHvbvMYMcOJxWwEgFnppSIzVoc7GCEMkguko5; unread={%22ub%22:%226945324a000000001f006964%22%2C%22ue%22:%22693c2652000000001e02d6e5%22%2C%22uc%22:23}; acw_tc=0a00dc2617663138850185186e1ad4adda9ee02e0f0f79f806643856a44235; loadts=1766313998521; websectiga=cf46039d1971c7b9a650d87269f31ac8fe3bf71d61ebf9d9a0a87efb414b816c; sec_poison_id=1c63e017-f4e7-4184-8d96-e5f4fc5b01d8' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0' \
  --compressed -s -o raw_page.html

# 纯净解析
python3 <<EOF
import json, re, sys

try:
    with open('raw_page.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(.*?)(?=<|;)', content, re.S)
    json_raw = match.group(1).replace(':undefined', ':null')
    data = json.loads(json_raw)
    
    # 提取正文
    detail_map = data.get('note', {}).get('noteDetailMap', {})
    note = list(detail_map.values())[0]['note']
    desc = note.get('desc', '')
    
    if "$MODE" == "-s":
        # 极简模式：只打印正文
        print(desc.strip())
    else:
        # 普通模式：带标题和格式
        print(f"\n📌 {note.get('title')}\n{'-'*40}\n{desc}\n")

except Exception as e:
    pass # 保持静默，符合极简原则

EOF

