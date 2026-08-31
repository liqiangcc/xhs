import java.util.*;

public final class ThreeSumReviewerTest {
    private static final Random RNG = new Random(0x62E1CBD2L);
    private static int exhaustiveCases = 0;

    private static void fail(String message) { throw new AssertionError(message); }

    private static String key(int x, int y, int z) {
        int[] a = {x, y, z};
        Arrays.sort(a);
        return a[0] + "," + a[1] + "," + a[2];
    }

    private static Set<String> oracle(int[] nums) {
        Set<String> out = new TreeSet<>();
        if (nums == null) return out;
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                for (int k = j + 1; k < nums.length; k++) {
                    if ((long) nums[i] + nums[j] + nums[k] == 0L) {
                        out.add(key(nums[i], nums[j], nums[k]));
                    }
                }
            }
        }
        return out;
    }

    private static Set<String> normalize(List<List<Integer>> rows) {
        if (rows == null) fail("result must not be null");
        Set<String> out = new TreeSet<>();
        for (List<Integer> row : rows) {
            if (row == null || row.size() != 3) fail("not a triplet: " + row);
            int x = row.get(0), y = row.get(1), z = row.get(2);
            if (!(x <= y && y <= z)) fail("triplet is not internally sorted: " + row);
            if ((long) x + y + z != 0L) fail("non-zero triplet: " + row);
            String k = key(x, y, z);
            if (!out.add(k)) fail("duplicate result triplet: " + k);
        }
        return out;
    }

    private static void check(int[] input, String label) {
        int[] before = input == null ? null : input.clone();
        Set<String> expected = oracle(input);
        Set<String> actual = normalize(ThreeSum.threeSum(input));
        if (!actual.equals(expected)) fail(label + " expected=" + expected + " actual=" + actual);
        if (input != null && !Arrays.equals(input, before)) fail(label + " mutated input");
    }

    private static void enumerate(int[] a, int pos) {
        if (pos == a.length) {
            exhaustiveCases++;
            check(a.clone(), "exhaustive-" + exhaustiveCases);
            return;
        }
        for (int v = -3; v <= 3; v++) {
            a[pos] = v;
            enumerate(a, pos + 1);
        }
    }

    private static int randomValue() {
        int mode = RNG.nextInt(20);
        if (mode == 0) return Integer.MIN_VALUE;
        if (mode == 1) return Integer.MAX_VALUE;
        return RNG.nextInt(41) - 20;
    }

    public static void main(String[] args) {
        check(new int[]{-1,0,1,2,-1,-4}, "classic");
        check(new int[]{0,0,0,0}, "all-zero");
        check(new int[]{1,2,-2,-1}, "none");
        check(new int[]{-2,0,0,2,2}, "dedupe-both-sides");
        check(new int[]{-4,-2,-2,-2,0,1,2,2,2,3,3,4}, "many-duplicates");
        check(new int[]{Integer.MIN_VALUE,1,Integer.MAX_VALUE}, "overflow-zero");
        check(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE,2,-3,-1}, "overflow-direction");
        check(new int[]{-1,-1,-1,2,2,2}, "duplicate-index-combos");
        check(new int[]{0,0}, "short-input");
        check(null, "null-input");

        for (int n = 0; n <= 5; n++) enumerate(new int[n], 0);
        if (exhaustiveCases != 19608) fail("exhaustive case count drift: " + exhaustiveCases);

        for (int i = 0; i < 25000; i++) {
            int n = RNG.nextInt(15);
            int[] a = new int[n];
            for (int j = 0; j < n; j++) a[j] = randomValue();
            check(a, "random-" + i);
        }

        System.out.println("PASS reviewer fixed=10 exhaustive=19608 random=25000 oracle=bruteforce-triples overflow=pass input_unchanged=pass dedupe=pass");
    }
}
