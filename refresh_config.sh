#!/bin/bash
# 职责：只负责从抓包结果中同步“通行证”
RAW_FILE="raw_curl.txt"
ENV_FILE="config_env.sh"

echo "正在从抓包结果同步认证信息..."

# 提取 Cookie, UA 和搜索专用签名
C=$(grep -oP "(?<=-b ').*?(?=')" $RAW_FILE || grep -oP "(?<=cookie: ).*?(?=')" $RAW_FILE)
UA=$(grep -oP "(?<=user-agent: ).*?(?=')" $RAW_FILE)
XS=$(grep -oP "(?<=x-s: ).*?(?=')" $RAW_FILE)
XSC=$(grep -oP "(?<=x-s-common: ).*?(?=')" $RAW_FILE)
XT=$(grep -oP "(?<=x-t: ).*?(?=')" $RAW_FILE)
# 提取捕获时的原始关键词，用于校验
OKW=$(grep -oP '(?<="keyword":")[^"]+' $RAW_FILE | head -1)

cat <<EOF > $ENV_FILE
export XHS_COOKIE='$C'
export XHS_UA='$UA'
export XHS_XS='$XS'
export XHS_S_COMMON='$XSC'
export XHS_XT='$XT'
export XHS_BIND_KW='$OKW'
EOF

echo "✅ 同步成功。当前签名绑定关键词：$OKW"
