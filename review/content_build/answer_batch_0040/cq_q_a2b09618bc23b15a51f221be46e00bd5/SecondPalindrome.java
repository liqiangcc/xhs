import java.util.*;

public final class SecondPalindrome {
    private static final class Range {
        final int left, right;
        Range(int left, int right) { this.left = left; this.right = right; }
        int length() { return right - left + 1; }
    }

    public static String solve(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        if (s.isEmpty()) return "";
        Range longest = scan(s, null, false);
        Range second = scan(s, longest, true);
        return second == null ? "" : s.substring(second.left, second.right + 1);
    }

    private static Range scan(String s, Range longest, boolean secondPass) {
        Range best = null;
        for (int c = 0; c < s.length(); c++) {
            best = expand(s, c, c, longest, secondPass, best);
            best = expand(s, c, c + 1, longest, secondPass, best);
        }
        return best;
    }

    private static Range expand(String s, int l, int r, Range longest,
                                boolean secondPass, Range best) {
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            if (!secondPass || eligible(l, r, longest)) best = better(best, l, r);
            l--;
            r++;
        }
        return best;
    }

    private static boolean eligible(int l, int r, Range longest) {
        int len = r - l + 1;
        boolean insideLongest = l >= longest.left && r <= longest.right;
        return len < longest.length() && !insideLongest;
    }

    private static Range better(Range best, int l, int r) {
        if (best == null || r - l > best.right - best.left ||
            (r - l == best.right - best.left && l < best.left)) return new Range(l, r);
        return best;
    }

    private static boolean palindrome(String s, int l, int r) {
        while (l < r) if (s.charAt(l++) != s.charAt(r--)) return false;
        return true;
    }

    private static String brute(String s) {
        if (s.isEmpty()) return "";
        Range longest = null;
        for (int l = 0; l < s.length(); l++) {
            for (int r = l; r < s.length(); r++) {
                if (palindrome(s, l, r)) longest = better(longest, l, r);
            }
        }
        Range second = null;
        for (int l = 0; l < s.length(); l++) {
            for (int r = l; r < s.length(); r++) {
                if (palindrome(s, l, r) && eligible(l, r, longest)) second = better(second, l, r);
            }
        }
        return second == null ? "" : s.substring(second.left, second.right + 1);
    }

    private static void enumerate(char[] a, int idx) {
        if (idx == a.length) {
            String s = new String(a);
            String got = solve(s), want = brute(s);
            if (!got.equals(want)) throw new AssertionError("mismatch s=" + s + " got=" + got + " want=" + want);
            return;
        }
        for (char ch : new char[]{'a','b','c'}) { a[idx] = ch; enumerate(a, idx + 1); }
    }

    public static void main(String[] args) {
        Map<String,String> cases = new LinkedHashMap<>();
        cases.put("", "");
        cases.put("a", "");
        cases.put("racecarxyzzyx", "xyzzyx");
        cases.put("babadxyzzyx", "bab");
        cases.put("aaaaabcc", "cc");
        cases.put("abacaba", "");
        for (Map.Entry<String,String> e : cases.entrySet()) {
            String got = solve(e.getKey());
            if (!got.equals(e.getValue())) throw new AssertionError("known s=" + e.getKey() + " got=" + got + " want=" + e.getValue());
        }
        for (int n = 0; n <= 8; n++) enumerate(new char[n], 0);
        try { solve(null); throw new AssertionError("null must reject"); } catch (IllegalArgumentException expected) {}
        System.out.println("PASS known-cases exhaustive-alphabet-abc-length-0..8 brute-oracle null=rejected explicit-tie-contract");
    }
}
