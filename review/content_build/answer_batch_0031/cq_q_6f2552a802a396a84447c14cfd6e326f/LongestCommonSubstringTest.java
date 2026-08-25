import java.util.Random;

public final class LongestCommonSubstringTest {
    private static void expect(String a, String b, int length) {
        var result = LongestCommonSubstring.solve(a, b);
        if (result.length() != length) throw new AssertionError(a + " / " + b + " => " + result);
        if (result.substring().length() != length) throw new AssertionError("substring length drift: " + result);
        if (!a.contains(result.substring()) || !b.contains(result.substring())) throw new AssertionError("not a common substring: " + result);
    }

    private static int bruteLength(String a, String b) {
        int best = 0;
        for (int i = 0; i < a.length(); i++) {
            for (int j = 0; j < b.length(); j++) {
                int k = 0;
                while (i + k < a.length() && j + k < b.length() && a.charAt(i + k) == b.charAt(j + k)) k++;
                if (k > best) best = k;
            }
        }
        return best;
    }

    private static String randomString(Random random, int length) {
        String alphabet = "abc";
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) sb.append(alphabet.charAt(random.nextInt(alphabet.length())));
        return sb.toString();
    }

    public static void main(String[] args) {
        expect("", "abc", 0);
        expect("abc", "xyz", 0);
        expect("abcdef", "zabcf", 3);
        expect("aaaa", "baaa", 3);
        expect("same", "same", 4);
        expect("abXYcd", "zzabqqcd", 2);
        try {
            LongestCommonSubstring.solve(null, "x");
            throw new AssertionError("null must be rejected");
        } catch (IllegalArgumentException expected) {}

        Random random = new Random(0x6f2552a8L);
        int cases = 3000;
        for (int t = 0; t < cases; t++) {
            String a = randomString(random, random.nextInt(8));
            String b = randomString(random, random.nextInt(8));
            int expected = bruteLength(a, b);
            var actual = LongestCommonSubstring.solve(a, b);
            if (actual.length() != expected) throw new AssertionError("oracle mismatch: " + a + " / " + b + " expected=" + expected + " actual=" + actual);
            if (!a.contains(actual.substring()) || !b.contains(actual.substring())) throw new AssertionError("oracle substring invalid");
        }
        System.out.println("PASS fixed=6 random-oracle=3000 empty=yes no-match=yes repeated=yes tie=yes null=rejected compression=reverse-j");
    }
}
