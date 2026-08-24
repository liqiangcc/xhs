import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import java.util.TreeSet;

public final class SortedPairSumTest {
    private static final int TARGET = 10;

    public static void main(String[] args) {
        int fixed = 0;
        fixed += check(null);
        fixed += check(new int[] {});
        fixed += check(new int[] {10});
        fixed += check(new int[] {1, 9});
        fixed += check(new int[] {1, 2, 3, 7, 8, 9});
        fixed += check(new int[] {1, 1, 5, 5, 5, 9, 9});
        fixed += check(new int[] {-10, -1, 0, 5, 10, 11, 20});
        fixed += check(new int[] {Integer.MIN_VALUE, -1, 0, 10, 11, Integer.MAX_VALUE});
        fixed += check(new int[] {1, 2, 3, 4});

        Random random = new Random(20260824L);
        int randomized = 5000;
        for (int round = 0; round < randomized; round++) {
            int n = random.nextInt(80);
            int[] input = new int[n];
            for (int i = 0; i < n; i++) {
                input[i] = random.nextInt(61) - 25;
            }
            Arrays.sort(input);
            check(input);
        }

        System.out.println(
            "PASS fixed=" + fixed
                + " randomized=" + randomized
                + " oracle=quadratic-unique-pairs target=10 mutation=none"
        );
    }

    private static int check(int[] input) {
        int[] before = input == null ? null : input.clone();
        List<int[]> actual = SortedPairSum.uniqueValuePairs(input, TARGET);
        List<int[]> expected = bruteForce(input, TARGET);

        if (!samePairs(actual, expected)) {
            throw new AssertionError(
                "pair mismatch input=" + Arrays.toString(input)
                    + " expected=" + render(expected)
                    + " actual=" + render(actual)
            );
        }
        if (input != null && !Arrays.equals(input, before)) {
            throw new AssertionError("input mutated");
        }
        return 1;
    }

    private static List<int[]> bruteForce(int[] input, int target) {
        List<int[]> result = new ArrayList<>();
        if (input == null) {
            return result;
        }
        TreeSet<String> seen = new TreeSet<>();
        for (int i = 0; i < input.length; i++) {
            for (int j = i + 1; j < input.length; j++) {
                if ((long) input[i] + input[j] == target) {
                    seen.add(input[i] + "," + input[j]);
                }
            }
        }
        for (String pair : seen) {
            String[] parts = pair.split(",", -1);
            result.add(new int[] {Integer.parseInt(parts[0]), Integer.parseInt(parts[1])});
        }
        result.sort((a, b) -> {
            int cmp = Integer.compare(a[0], b[0]);
            return cmp != 0 ? cmp : Integer.compare(a[1], b[1]);
        });
        return result;
    }

    private static boolean samePairs(List<int[]> a, List<int[]> b) {
        if (a.size() != b.size()) {
            return false;
        }
        for (int i = 0; i < a.size(); i++) {
            if (!Arrays.equals(a.get(i), b.get(i))) {
                return false;
            }
        }
        return true;
    }

    private static String render(List<int[]> pairs) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < pairs.size(); i++) {
            if (i > 0) out.append(", ");
            out.append(Arrays.toString(pairs.get(i)));
        }
        return out.append(']').toString();
    }
}
