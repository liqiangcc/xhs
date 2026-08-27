import java.util.HashMap;
import java.util.Map;

public final class LongestUniqueSubstringValidation {
    static final class Solution {
        static String longestUniqueSubstring(String s) {
            if (s == null) {
                throw new IllegalArgumentException("s must not be null");
            }

            int[] codePoints = s.codePoints().toArray();
            Map<Integer, Integer> lastSeen = new HashMap<>();
            int left = 0;
            int bestStart = 0;
            int bestLength = 0;

            for (int right = 0; right < codePoints.length; right++) {
                int cp = codePoints[right];
                Integer prev = lastSeen.get(cp);
                if (prev != null && prev >= left) {
                    left = prev + 1;
                }
                lastSeen.put(cp, right);

                int length = right - left + 1;
                if (length > bestLength) {
                    bestLength = length;
                    bestStart = left;
                }
            }
            return new String(codePoints, bestStart, bestLength);
        }
    }

    static String oracle(String s) {
        if (s == null) {
            throw new IllegalArgumentException("s must not be null");
        }
        int[] cps = s.codePoints().toArray();
        int bestStart = 0;
        int bestLength = 0;
        for (int start = 0; start < cps.length; start++) {
            java.util.HashSet<Integer> seen = new java.util.HashSet<>();
            for (int end = start; end < cps.length; end++) {
                if (!seen.add(cps[end])) break;
                int length = end - start + 1;
                if (length > bestLength) {
                    bestLength = length;
                    bestStart = start;
                }
            }
        }
        return new String(cps, bestStart, bestLength);
    }

    static void check(String input, String expected) {
        String actual = Solution.longestUniqueSubstring(input);
        if (!actual.equals(expected)) {
            throw new AssertionError("input=" + input + " expected=" + expected + " actual=" + actual);
        }
        String independent = oracle(input);
        if (!actual.equals(independent)) {
            throw new AssertionError("oracle mismatch input=" + input + " expected=" + independent + " actual=" + actual);
        }
    }

    static String build(int[] alphabet, int value, int length) {
        int[] cps = new int[length];
        for (int i = length - 1; i >= 0; i--) {
            cps[i] = alphabet[value % alphabet.length];
            value /= alphabet.length;
        }
        return new String(cps, 0, cps.length);
    }

    public static void main(String[] args) {
        check("", "");
        check("abcabcbb", "abc");
        check("bbbbb", "b");
        check("pwwkew", "wke");
        check("abba", "ab");
        check("dvdf", "vdf");
        check("a😀b😀c", "a😀b");
        check("😀😀", "😀");
        check("😀a😀bc", "a😀bc");

        boolean nullRejected = false;
        try {
            Solution.longestUniqueSubstring(null);
        } catch (IllegalArgumentException expected) {
            nullRejected = true;
        }
        if (!nullRejected) throw new AssertionError("null must be explicitly rejected");

        int[] alphabet = {'a', 'b', 'c', 0x1F600};
        int exhaustive = 0;
        for (int length = 0; length <= 7; length++) {
            int count = 1;
            for (int i = 0; i < length; i++) count *= alphabet.length;
            for (int value = 0; value < count; value++) {
                String input = build(alphabet, value, length);
                String actual = Solution.longestUniqueSubstring(input);
                String expected = oracle(input);
                if (!actual.equals(expected)) {
                    throw new AssertionError("exhaustive mismatch input=" + input + " expected=" + expected + " actual=" + actual);
                }
                exhaustive++;
            }
        }

        if (exhaustive != 21845) throw new AssertionError("unexpected exhaustive count: " + exhaustive);
        System.out.println("PASS fixed=9 exhaustive=21845 unicode-code-point=covered leftmost-tie=covered null=rejected");
    }
}
