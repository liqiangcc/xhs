public final class LongestPalindromicSubsequenceTest {
    public static void main(String[] args) {
        assertEq(4, LongestPalindromicSubsequence.longestPalindromeSubseq("bbbab"), "official example 1");
        assertEq(2, LongestPalindromicSubsequence.longestPalindromeSubseq("cbbd"), "official example 2");
        assertEq(1, LongestPalindromicSubsequence.longestPalindromeSubseq("a"), "single");
        assertEq(5, LongestPalindromicSubsequence.longestPalindromeSubseq("abcba"), "whole palindrome");
        assertEq(1, LongestPalindromicSubsequence.longestPalindromeSubseq("abc"), "all distinct");
        assertEq(0, LongestPalindromicSubsequence.longestPalindromeSubseq(""), "empty extension");

        int checked = 0;
        for (int len = 0; len <= 8; len++) {
            int total = pow(3, len);
            for (int mask = 0; mask < total; mask++) {
                String s = ternaryString(mask, len);
                int actual = LongestPalindromicSubsequence.longestPalindromeSubseq(s);
                int expected = bruteForce(s);
                if (actual != expected) {
                    throw new AssertionError("mismatch s=" + s + " expected=" + expected + " actual=" + actual);
                }
                checked++;
            }
        }
        System.out.println("PASS exhaustive_strings=" + checked + " alphabet=abc max_len=8");
    }

    private static int bruteForce(String s) {
        int n = s.length();
        int best = 0;
        int total = 1 << n;
        for (int mask = 0; mask < total; mask++) {
            int length = Integer.bitCount(mask);
            if (length <= best) continue;
            char[] seq = new char[length];
            int p = 0;
            for (int i = 0; i < n; i++) {
                if ((mask & (1 << i)) != 0) seq[p++] = s.charAt(i);
            }
            if (isPalindrome(seq)) best = length;
        }
        return best;
    }

    private static boolean isPalindrome(char[] seq) {
        for (int i = 0, j = seq.length - 1; i < j; i++, j--) {
            if (seq[i] != seq[j]) return false;
        }
        return true;
    }

    private static int pow(int base, int exp) {
        int result = 1;
        for (int i = 0; i < exp; i++) result *= base;
        return result;
    }

    private static String ternaryString(int value, int len) {
        char[] chars = new char[len];
        for (int i = 0; i < len; i++) {
            chars[i] = (char) ('a' + (value % 3));
            value /= 3;
        }
        return new String(chars);
    }

    private static void assertEq(int expected, int actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
    }
}
