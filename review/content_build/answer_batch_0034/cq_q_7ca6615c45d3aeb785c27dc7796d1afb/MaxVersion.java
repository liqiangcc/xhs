import java.util.List;

public final class MaxVersion {
    public static String maxVersion(List<String> versions) {
        if (versions == null || versions.isEmpty()) {
            throw new IllegalArgumentException("versions must not be empty");
        }
        String best = requireValid(versions.get(0));
        for (int i = 1; i < versions.size(); i++) {
            String current = requireValid(versions.get(i));
            if (compareVersion(current, best) > 0) {
                best = current;
            }
        }
        return best;
    }

    public static int compareVersion(String a, String b) {
        requireValid(a);
        requireValid(b);
        int i = 0, j = 0;
        while (i < a.length() || j < b.length()) {
            int aEnd = nextDot(a, i);
            int bEnd = nextDot(b, j);
            int cmp = compareRevision(a, i, aEnd, b, j, bEnd);
            if (cmp != 0) return cmp;
            i = aEnd < a.length() ? aEnd + 1 : a.length();
            j = bEnd < b.length() ? bEnd + 1 : b.length();
        }
        return 0;
    }

    private static int nextDot(String s, int start) {
        if (start >= s.length()) return s.length();
        int p = start;
        while (p < s.length() && s.charAt(p) != '.') p++;
        return p;
    }

    private static int compareRevision(
            String a, int aStart, int aEnd,
            String b, int bStart, int bEnd) {
        while (aStart < aEnd && a.charAt(aStart) == '0') aStart++;
        while (bStart < bEnd && b.charAt(bStart) == '0') bStart++;
        int aLen = aEnd - aStart;
        int bLen = bEnd - bStart;
        if (aLen != bLen) return Integer.compare(aLen, bLen);
        for (int k = 0; k < aLen; k++) {
            char x = a.charAt(aStart + k), y = b.charAt(bStart + k);
            if (x != y) return Character.compare(x, y);
        }
        return 0;
    }

    private static String requireValid(String s) {
        if (s == null || s.isEmpty() || s.charAt(0) == '.' || s.charAt(s.length() - 1) == '.') {
            throw new IllegalArgumentException("invalid version");
        }
        boolean needDigit = true;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '.') {
                if (needDigit) throw new IllegalArgumentException("invalid version");
                needDigit = true;
            } else if (ch >= '0' && ch <= '9') {
                needDigit = false;
            } else {
                throw new IllegalArgumentException("invalid version");
            }
        }
        if (needDigit) throw new IllegalArgumentException("invalid version");
        return s;
    }
}
