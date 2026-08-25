import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;

public final class StringPermutationsIndependentTest {
    private static boolean nextPermutation(int[] a) {
        int i = a.length - 2;
        while (i >= 0 && a[i] >= a[i + 1]) i--;
        if (i < 0) return false;
        int j = a.length - 1;
        while (a[j] <= a[i]) j--;
        int t = a[i]; a[i] = a[j]; a[j] = t;
        for (int l = i + 1, r = a.length - 1; l < r; l++, r--) {
            t = a[l]; a[l] = a[r]; a[r] = t;
        }
        return true;
    }

    private static Set<String> oracle(String input) {
        int[] a = input.codePoints().sorted().toArray();
        Set<String> out = new HashSet<>();
        out.add(new String(a, 0, a.length));
        while (nextPermutation(a)) out.add(new String(a, 0, a.length));
        return out;
    }

    private static String shuffledDistinct(int n, Random rnd) {
        int[] pool = {'a','b','c','d','e','f','g','h','你',0x1F642};
        List<Integer> xs = new ArrayList<>();
        for (int cp : pool) xs.add(cp);
        Collections.shuffle(xs, rnd);
        int[] a = new int[n];
        for (int i = 0; i < n; i++) a[i] = xs.get(i);
        return new String(a, 0, a.length);
    }

    public static void main(String[] args) {
        Random rnd = new Random(20260825L);
        int cases = 0;
        for (int n = 0; n <= 8; n++) {
            int rounds = n <= 6 ? 20 : 4;
            for (int r = 0; r < rounds; r++) {
                String input = shuffledDistinct(n, rnd);
                Set<String> expected = oracle(input);
                List<String> actualList = StringPermutations.permutations(input);
                Set<String> actual = new HashSet<>(actualList);
                if (actual.size() != actualList.size()) throw new AssertionError("candidate duplicated output: " + input);
                if (!actual.equals(expected)) throw new AssertionError("set mismatch n=" + n + " input=" + input);
                cases++;
            }
        }
        boolean duplicateRejected = false;
        try { StringPermutations.permutations("🙂a🙂"); } catch (IllegalArgumentException e) { duplicateRejected = true; }
        if (!duplicateRejected) throw new AssertionError("duplicate code point not rejected");
        boolean nullRejected = false;
        try { StringPermutations.permutations(null); } catch (NullPointerException e) { nullRejected = true; }
        if (!nullRejected) throw new AssertionError("null not rejected");
        System.out.println("PASS actual-candidate lexicographic-independent-oracle cases=" + cases + " n=0..8 mixed-unicode duplicate-codepoint=rejected null=rejected");
    }
}
