import java.util.*;

public class writer_validation {
    static List<List<Integer>> nonEmptySubsets(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        backtrack(nums, 0, new ArrayList<>(), result);
        return result;
    }

    static void backtrack(
            int[] nums,
            int start,
            List<Integer> path,
            List<List<Integer>> result) {
        for (int i = start; i < nums.length; i++) {
            path.add(nums[i]);
            result.add(new ArrayList<>(path));
            backtrack(nums, i + 1, path, result);
            path.remove(path.size() - 1);
        }
    }

    static List<List<Integer>> oracle(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        int total = 1 << nums.length;
        for (int mask = 1; mask < total; mask++) {
            List<Integer> subset = new ArrayList<>();
            for (int i = 0; i < nums.length; i++) {
                if ((mask & (1 << i)) != 0) subset.add(nums[i]);
            }
            result.add(subset);
        }
        return result;
    }

    static Map<List<Integer>, Integer> multiset(List<List<Integer>> rows) {
        Map<List<Integer>, Integer> result = new HashMap<>();
        for (List<Integer> row : rows) {
            result.merge(List.copyOf(row), 1, Integer::sum);
        }
        return result;
    }

    static void check(int[] nums) {
        List<List<Integer>> got = nonEmptySubsets(nums);
        List<List<Integer>> expected = oracle(nums);
        if (got.size() != expected.size()) {
            throw new AssertionError("count mismatch: " + Arrays.toString(nums));
        }
        if (!multiset(got).equals(multiset(expected))) {
            throw new AssertionError("content mismatch: " + Arrays.toString(nums));
        }
        for (List<Integer> row : got) {
            if (row.isEmpty()) throw new AssertionError("empty subset emitted");
        }
    }

    public static void main(String[] args) {
        check(new int[]{});
        check(new int[]{1});
        check(new int[]{1, 2, 3});
        check(new int[]{1, 1});
        check(new int[]{0, -1, 2, 2});

        Random random = new Random(20260826L);
        int randomized = 0;
        for (int t = 0; t < 2000; t++) {
            int n = random.nextInt(11);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = random.nextInt(7) - 3;
            check(nums);
            randomized++;
        }

        int[] ten = new int[10];
        for (int i = 0; i < ten.length; i++) ten[i] = i;
        if (nonEmptySubsets(ten).size() != 1023) {
            throw new AssertionError("n=10 must produce 1023 non-empty subsets");
        }

        System.out.println(
                "PASS deterministic=5 randomized=" + randomized
                        + " n10=1023 duplicate-position-semantics=verified empty-subset=excluded");
    }
}
