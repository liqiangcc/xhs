import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class StringPermutationsFixture {
    private static long factorial(int n) {
        long x = 1;
        for (int i = 2; i <= n; i++) x *= i;
        return x;
    }

    private static String canonicalKey(String s) {
        int[] cps = s.codePoints().sorted().toArray();
        return new String(cps, 0, cps.length);
    }

    private static void check(String input) {
        List<String> out = StringPermutations.permutations(input);
        int n = input.codePointCount(0, input.length());
        if (out.size() != factorial(n)) throw new AssertionError("count " + input + " -> " + out.size());
        Set<String> unique = new HashSet<>(out);
        if (unique.size() != out.size()) throw new AssertionError("duplicate permutation: " + input);
        String expectedChars = canonicalKey(input);
        for (String s : out) {
            if (s.codePointCount(0, s.length()) != n) throw new AssertionError("length drift");
            if (!canonicalKey(s).equals(expectedChars)) throw new AssertionError("character drift: " + s);
        }
    }

    public static void main(String[] args) {
        List<String> abc = StringPermutations.permutations("abc");
        Set<String> expected = Set.of("abc", "acb", "bac", "bca", "cab", "cba");
        if (!new HashSet<>(abc).equals(expected)) throw new AssertionError("abc set mismatch: " + abc);
        if (!StringPermutations.permutations("").equals(List.of(""))) throw new AssertionError("empty contract");
        if (!StringPermutations.permutations("你a🙂").contains("🙂a你")) throw new AssertionError("unicode code point handling");
        boolean duplicateRejected = false;
        try { StringPermutations.permutations("aba"); } catch (IllegalArgumentException e) { duplicateRejected = true; }
        if (!duplicateRejected) throw new AssertionError("duplicate precondition should fail closed");
        for (int n = 0; n <= 8; n++) {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < n; i++) sb.append((char)('a' + i));
            check(sb.toString());
        }
        System.out.println("PASS exact-abc empty=one unicode-codepoints duplicate-input=rejected counts=n! unique-and-multiset n=0..8");
    }
}
