import java.util.Random;

public final class LongestPalindromicSubstringValidation {
    static String longestPalindrome(String s) {
        if (s == null || s.length() < 2) return s == null ? "" : s;
        int bestStart = 0;
        int bestLen = 1;
        for (int center = 0; center < s.length(); center++) {
            int[] odd = expand(s, center, center);
            int[] even = expand(s, center, center + 1);
            if (better(odd[0], odd[1], bestStart, bestLen)) {
                bestStart = odd[0]; bestLen = odd[1];
            }
            if (better(even[0], even[1], bestStart, bestLen)) {
                bestStart = even[0]; bestLen = even[1];
            }
        }
        return s.substring(bestStart, bestStart + bestLen);
    }

    private static int[] expand(String s, int left, int right) {
        while (left >= 0 && right < s.length() && s.charAt(left) == s.charAt(right)) {
            left--; right++;
        }
        return new int[]{left + 1, right - left - 1};
    }

    private static boolean better(int start, int len, int bestStart, int bestLen) {
        return len > bestLen || (len == bestLen && start < bestStart);
    }

    static String brute(String s) {
        if (s == null || s.isEmpty()) return s == null ? "" : s;
        int bestStart = 0, bestLen = 1;
        for (int l = 0; l < s.length(); l++) {
            for (int r = l; r < s.length(); r++) {
                if (isPalindrome(s, l, r)) {
                    int len = r - l + 1;
                    if (len > bestLen || (len == bestLen && l < bestStart)) {
                        bestStart = l; bestLen = len;
                    }
                }
            }
        }
        return s.substring(bestStart, bestStart + bestLen);
    }

    static boolean isPalindrome(String s, int l, int r) {
        while (l < r) if (s.charAt(l++) != s.charAt(r--)) return false;
        return true;
    }

    static void expect(String input, String expected) {
        String actual = longestPalindrome(input);
        if (!actual.equals(expected)) throw new AssertionError("input=" + input + " expected=" + expected + " actual=" + actual);
        String slow = brute(input);
        if (!actual.equals(slow)) throw new AssertionError("oracle mismatch input=" + input + " fast=" + actual + " slow=" + slow);
    }

    public static void main(String[] args) {
        expect("babad", "bab");
        expect("cbbd", "bb");
        expect("a", "a");
        expect("", "");
        expect("ac", "a");
        expect("aaaa", "aaaa");
        expect("forgeeksskeegfor", "geeksskeeg");
        if (!longestPalindrome(null).equals("")) throw new AssertionError("null boundary failed");

        Random random = new Random(8307350L);
        String alphabet = "abca";
        int randomized = 5000;
        for (int t = 0; t < randomized; t++) {
            int n = random.nextInt(16);
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < n; i++) sb.append(alphabet.charAt(random.nextInt(alphabet.length())));
            String s = sb.toString();
            String fast = longestPalindrome(s);
            String slow = brute(s);
            if (!fast.equals(slow)) throw new AssertionError("random oracle mismatch input=" + s + " fast=" + fast + " slow=" + slow);
        }
        System.out.println("PASS fixed=7 randomized=5000 oracle=bruteforce earliest-tie=true odd-even=true empty-null=true");
    }
}
