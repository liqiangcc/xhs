import java.util.Random;

public final class LongestCommonSubsequenceWriterTest {
    private static final Random RNG = new Random(0x62006A7CL);
    private static final char[] ALPHABET = {'a','b','c','d'};

    private static int oracle(String a, String b) {
        int[][] dp = new int[a.length() + 1][b.length() + 1];
        for (int i = 1; i <= a.length(); i++) {
            for (int j = 1; j <= b.length(); j++) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) dp[i][j] = dp[i - 1][j - 1] + 1;
                else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        return dp[a.length()][b.length()];
    }

    private static void check(String a, String b, int expected, String label) {
        int actual = LongestCommonSubsequence.lcsLength(a, b);
        if (actual != expected) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        int reversed = LongestCommonSubsequence.lcsLength(b, a);
        if (reversed != expected) throw new AssertionError(label + " symmetry expected=" + expected + " actual=" + reversed);
    }

    private static String randomString(int maxLen) {
        int len = RNG.nextInt(maxLen + 1);
        StringBuilder sb = new StringBuilder(len);
        for (int i = 0; i < len; i++) sb.append(ALPHABET[RNG.nextInt(ALPHABET.length)]);
        return sb.toString();
    }

    public static void main(String[] args) {
        check("", "", 0, "both-empty");
        check("abc", "", 0, "one-empty");
        check("abcde", "ace", 3, "classic");
        check("abc", "abc", 3, "identical");
        check("abc", "def", 0, "disjoint");
        check("abc", "bac", 2, "cross-order");
        check("aaaa", "aa", 2, "repeated");
        check("XMJYAUZ", "MZJAWXU", 4, "nontrivial");
        boolean threw = false;
        try { LongestCommonSubsequence.lcsLength(null, "x"); } catch (IllegalArgumentException expected) { threw = true; }
        if (!threw) throw new AssertionError("null contract must throw IllegalArgumentException");

        for (int i = 0; i < 30000; i++) {
            String a = randomString(12);
            String b = randomString(12);
            int expected = oracle(a, b);
            check(a, b, expected, "random-" + i);
        }
        System.out.println("PASS fixed=8 random=30000 oracle=2d-dp symmetry=preserved empty=0 repeated=preserved");
    }
}
