import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

public final class StringPermutations {
    private StringPermutations() {}

    public static List<String> permutations(String input) {
        Objects.requireNonNull(input, "input");
        int[] codePoints = input.codePoints().toArray();
        Set<Integer> seen = new HashSet<>();
        for (int cp : codePoints) {
            if (!seen.add(cp)) {
                throw new IllegalArgumentException("input must contain distinct characters");
            }
        }
        List<String> out = new ArrayList<>();
        backtrack(codePoints, 0, out);
        return out;
    }

    private static void backtrack(int[] a, int first, List<String> out) {
        if (first == a.length) {
            out.add(new String(a, 0, a.length));
            return;
        }
        for (int i = first; i < a.length; i++) {
            swap(a, first, i);
            backtrack(a, first + 1, out);
            swap(a, first, i);
        }
    }

    private static void swap(int[] a, int i, int j) {
        int t = a[i];
        a[i] = a[j];
        a[j] = t;
    }
}
