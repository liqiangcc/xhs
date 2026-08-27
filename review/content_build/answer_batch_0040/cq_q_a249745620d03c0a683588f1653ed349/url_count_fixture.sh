#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/urls.txt" <<'EOF'
https://a.example/x
https://b.example/y
https://a.example/x

https://c.example/z
https://b.example/y
https://a.example/x
EOF
LC_ALL=C awk 'NF {print $0}' "$tmp/urls.txt" | sort | uniq -c | awk '{$1=$1; print}' | sort -nr > "$tmp/actual"
cat > "$tmp/expected" <<'EOF'
3 https://a.example/x
2 https://b.example/y
1 https://c.example/z
EOF
diff -u "$tmp/expected" "$tmp/actual"
echo 'PASS non-adjacent-duplicates=grouped blank-lines=ignored counts=3,2,1'
