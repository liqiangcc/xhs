import java.util.*;

public final class PermutationsValidation {
    static final class Permutations {
        static List<List<Integer>> permute(int[] nums) {
            if (nums == null) throw new IllegalArgumentException("nums must not be null");
            List<List<Integer>> result = new ArrayList<>();
            boolean[] used = new boolean[nums.length];
            backtrack(nums, used, new ArrayList<>(), result);
            return result;
        }

        private static void backtrack(int[] nums, boolean[] used, List<Integer> path, List<List<Integer>> result) {
            if (path.size() == nums.length) {
                result.add(new ArrayList<>(path));
                return;
            }
            for (int i = 0; i < nums.length; i++) {
                if (used[i]) continue;
                used[i] = true;
                path.add(nums[i]);
                backtrack(nums, used, path, result);
                path.remove(path.size() - 1);
                used[i] = false;
            }
        }
    }

    static List<List<Integer>> lexicographicOracle(int[] input) {
        int[] a = input.clone();
        Arrays.sort(a);
        List<List<Integer>> out = new ArrayList<>();
        do {
            List<Integer> row = new ArrayList<>(a.length);
            for (int value : a) row.add(value);
            out.add(row);
        } while (nextPermutation(a));
        return out;
    }

    static boolean nextPermutation(int[] a) {
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

    static long factorial(int n) {
        long value = 1;
        for (int i = 2; i <= n; i++) value *= i;
        return value;
    }

    static void assertCase(int[] input) {
        List<List<Integer>> actual = Permutations.permute(input);
        List<List<Integer>> expected = lexicographicOracle(input);
        if (actual.size() != factorial(input.length)) {
            throw new AssertionError("wrong count n=" + input.length + " actual=" + actual.size());
        }
        Set<List<Integer>> actualSet = new HashSet<>(actual);
        Set<List<Integer>> expectedSet = new HashSet<>(expected);
        if (actualSet.size() != actual.size()) throw new AssertionError("duplicate result rows for " + Arrays.toString(input));
        if (!actualSet.equals(expectedSet)) throw new AssertionError("oracle mismatch for " + Arrays.toString(input));
        for (List<Integer> row : actual) {
            if (row.size() != input.length) throw new AssertionError("wrong row length");
        }
    }

    public static void main(String[] args) {
        for (int n = 0; n <= 8; n++) {
            int[] input = new int[n];
            for (int i = 0; i < n; i++) input[i] = i - 4;
            assertCase(input);
        }
        Random random = new Random(20260826L);
        for (int round = 0; round < 120; round++) {
            int n = random.nextInt(8);
            List<Integer> pool = new ArrayList<>();
            for (int v = -20; v <= 20; v++) pool.add(v);
            Collections.shuffle(pool, random);
            int[] input = new int[n];
            for (int i = 0; i < n; i++) input[i] = pool.get(i);
            for (int i = input.length - 1; i > 0; i--) {
                int j = random.nextInt(i + 1);
                int t = input[i]; input[i] = input[j]; input[j] = t;
            }
            assertCase(input);
        }
        boolean nullRejected = false;
        try { Permutations.permute(null); } catch (IllegalArgumentException expected) { nullRejected = true; }
        if (!nullRejected) throw new AssertionError("null contract not enforced");
        List<List<Integer>> empty = Permutations.permute(new int[0]);
        if (empty.size() != 1 || !empty.get(0).isEmpty()) throw new AssertionError("empty permutation contract failed");
        System.out.println("PASS fixed-n=0..8 randomized=120 oracle=lexicographic-next-permutation distinct-input=true count-factorial=true no-duplicates=true empty-one=true null-rejected=true");
    }
}
