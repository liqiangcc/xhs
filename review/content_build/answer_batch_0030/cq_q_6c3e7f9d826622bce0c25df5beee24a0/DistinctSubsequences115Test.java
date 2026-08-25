public final class DistinctSubsequences115Test {
    public static void main(String[] args) {
        eq(3, DistinctSubsequences115.numDistinct("rabbbit", "rabbit"), "official rabbit");
        eq(5, DistinctSubsequences115.numDistinct("babgbag", "bag"), "official bag");
        eq(0, DistinctSubsequences115.numDistinct("abc", "abcd"), "target longer");
        eq(1, DistinctSubsequences115.numDistinct("abc", "abc"), "equal strings");
        eq(10, DistinctSubsequences115.numDistinct("aaaaa", "aa"), "equal chars choose positions");
        eq(1, DistinctSubsequences115.numDistinct("abc", ""), "generalized empty target");
        eq(0, DistinctSubsequences115.numDistinct("", "a"), "generalized empty source");
        eq(0, DistinctSubsequences115.numDistinct("a".repeat(1000), "a".repeat(20) + "b"), "huge intermediate prefix with zero final");
        exhaustiveBinaryOracle();
        throwsArithmetic(() -> DistinctSubsequences115.numDistinct("a".repeat(50), "a".repeat(25)));
        throwsIAE(() -> DistinctSubsequences115.numDistinct(null, "a"));
        System.out.println("PASS official=2 combinatorial=yes empty-extension=yes saturation-prefix=yes exhaustive-binary=yes overflow-contract=yes invalid=yes");
    }

    private static void exhaustiveBinaryOracle() {
        for (int n = 0; n <= 8; n++) {
            for (int sm = 0; sm < (1 << n); sm++) {
                String s = binaryString(n, sm);
                for (int m = 0; m <= Math.min(5, n + 1); m++) {
                    for (int tm = 0; tm < (1 << m); tm++) {
                        String t = binaryString(m, tm);
                        int expected = brute(s, t, 0, 0);
                        int actual = DistinctSubsequences115.numDistinct(s, t);
                        if (expected != actual) throw new AssertionError("oracle s=" + s + " t=" + t + " expected=" + expected + " actual=" + actual);
                    }
                }
            }
        }
    }

    private static int brute(String s, String t, int i, int j) {
        if (j == t.length()) return 1;
        if (s.length() - i < t.length() - j) return 0;
        if (i == s.length()) return 0;
        int count = brute(s, t, i + 1, j);
        if (s.charAt(i) == t.charAt(j)) count += brute(s, t, i + 1, j + 1);
        return count;
    }

    private static String binaryString(int len, int mask) {
        StringBuilder b = new StringBuilder(len);
        for (int i = 0; i < len; i++) b.append(((mask >>> i) & 1) == 0 ? 'a' : 'b');
        return b.toString();
    }

    private static void eq(int expected, int actual, String label) {
        if (expected != actual) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
    }
    private static void throwsArithmetic(Runnable r) { try { r.run(); throw new AssertionError("expected ArithmeticException"); } catch (ArithmeticException expected) {} }
    private static void throwsIAE(Runnable r) { try { r.run(); throw new AssertionError("expected IllegalArgumentException"); } catch (IllegalArgumentException expected) {} }
}
