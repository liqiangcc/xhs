#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cat > "$tmp/input" <<'EOF'
https://b.example/y
https://a.example/x
https://c.example/z
https://a.example/x

https://b.example/y
https://a.example/x
https://d.example/q?x=1
https://d.example/q?x=2
EOF
LC_ALL=C awk 'NF {print $0}' "$tmp/input" | sort | uniq -c | awk '{$1=$1; print}' | sort -k2,2 > "$tmp/pipeline"
awk 'NF {count[$0]++} END {for (u in count) print count[u], u}' "$tmp/input" | LC_ALL=C sort -k2,2 > "$tmp/oracle"
diff -u "$tmp/oracle" "$tmp/pipeline"
grep -Fxq '3 https://a.example/x' "$tmp/pipeline"
grep -Fxq '2 https://b.example/y' "$tmp/pipeline"
grep -Fxq '1 https://c.example/z' "$tmp/pipeline"
grep -Fxq '1 https://d.example/q?x=1' "$tmp/pipeline"
grep -Fxq '1 https://d.example/q?x=2' "$tmp/pipeline"
test "$(wc -l < "$tmp/pipeline")" -eq 5
echo 'PASS pipeline=independent-awk-map counts=3,2,1 query-variants=distinct blank-lines=ignored'
