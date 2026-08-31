#!/usr/bin/env python3
"""Make the Batch 0062 LCS answer snippet a standalone compilable Java class."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CID = 'cq_q_6a7c7f58ad4a4828e2c984b668d7ba32'
CANDIDATE = Path(f'review/candidates/answers/{CID}.md')
BUILDER = Path('scripts/content/build_batch_0062_lcs.py')
WRITER_RESEARCH = Path(f'review/content_build/answer_batch_0062/{CID}/writer_research.json')

OLD = r'''```java
public static int lcsLength(String first, String second) {
    if (first == null || second == null) {
        throw new IllegalArgumentException("inputs must be non-null");
    }

    String rows = first;
    String cols = second;
    if (rows.length() < cols.length()) {
        String tmp = rows;
        rows = cols;
        cols = tmp;
    }

    int[] dp = new int[cols.length() + 1];
    for (int i = 1; i <= rows.length(); i++) {
        int prevDiag = 0;
        for (int j = 1; j <= cols.length(); j++) {
            int oldUp = dp[j];
            if (rows.charAt(i - 1) == cols.charAt(j - 1)) {
                dp[j] = prevDiag + 1;
            } else {
                dp[j] = Math.max(dp[j], dp[j - 1]);
            }
            prevDiag = oldUp;
        }
    }
    return dp[cols.length()];
}
```'''

NEW = r'''```java
public final class LongestCommonSubsequence {
    private LongestCommonSubsequence() {}

    public static int lcsLength(String first, String second) {
        if (first == null || second == null) {
            throw new IllegalArgumentException("inputs must be non-null");
        }

        String rows = first;
        String cols = second;
        if (rows.length() < cols.length()) {
            String tmp = rows;
            rows = cols;
            cols = tmp;
        }

        int[] dp = new int[cols.length() + 1];
        for (int i = 1; i <= rows.length(); i++) {
            int prevDiag = 0;
            for (int j = 1; j <= cols.length(); j++) {
                int oldUp = dp[j];
                if (rows.charAt(i - 1) == cols.charAt(j - 1)) {
                    dp[j] = prevDiag + 1;
                } else {
                    dp[j] = Math.max(dp[j], dp[j - 1]);
                }
                prevDiag = oldUp;
            }
        }
        return dp[cols.length()];
    }
}
```'''


def replace_once(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    if NEW in text:
        return
    count = text.count(OLD)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one method-only Java block, found {count}')
    path.write_text(text.replace(OLD, NEW, 1), encoding='utf-8')


def main() -> int:
    replace_once(CANDIDATE)
    replace_once(BUILDER)
    digest = hashlib.sha256(CANDIDATE.read_bytes()).hexdigest()
    research = json.loads(WRITER_RESEARCH.read_text(encoding='utf-8'))
    research['candidate_sha256'] = digest
    WRITER_RESEARCH.write_text(json.dumps(research, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS standalone-java-class candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
