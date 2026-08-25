import java.util.*;

public final class ModeMedianTest {
    static void check(int[] a, List<Integer> modes, double median) {
        ModeMedian.Result r = ModeMedian.solve(a);
        if (!r.modes.equals(modes)) {
            throw new AssertionError(Arrays.toString(a) + " modes=" + r.modes + " expected=" + modes);
        }
        if (Double.compare(r.median, median) != 0) {
            throw new AssertionError(Arrays.toString(a) + " median=" + r.median + " expected=" + median);
        }
    }

    static ModeMedian.Result oracle(int[] nums) {
        TreeMap<Integer, Integer> freq = new TreeMap<>();
        for (int x : nums) freq.put(x, freq.getOrDefault(x, 0) + 1);
        int max = Collections.max(freq.values());
        List<Integer> modes = new ArrayList<>();
        for (Map.Entry<Integer, Integer> e : freq.entrySet()) {
            if (e.getValue() == max) modes.add(e.getKey());
        }
        int k = modes.size();
        double median = (k % 2 == 1)
                ? modes.get(k / 2)
                : ((long) modes.get(k / 2 - 1) + modes.get(k / 2)) / 2.0;
        return new ModeMedian.Result(modes, median);
    }

    static void exhaustive(int maxLen, int[] alphabet) {
        for (int n = 1; n <= maxLen; n++) {
            int total = 1;
            for (int i = 0; i < n; i++) total *= alphabet.length;
            for (int mask = 0; mask < total; mask++) {
                int t = mask;
                int[] a = new int[n];
                for (int i = 0; i < n; i++) {
                    a[i] = alphabet[t % alphabet.length];
                    t /= alphabet.length;
                }
                ModeMedian.Result got = ModeMedian.solve(a);
                ModeMedian.Result expected = oracle(a);
                if (!got.modes.equals(expected.modes) || Double.compare(got.median, expected.median) != 0) {
                    throw new AssertionError("exhaustive mismatch " + Arrays.toString(a));
                }
            }
        }
    }

    public static void main(String[] args) {
        check(new int[]{1, 1, 2, 3}, Arrays.asList(1), 1.0);
        check(new int[]{1, 1, 2, 2, 3}, Arrays.asList(1, 2), 1.5);
        check(new int[]{-5, -5, 7, 7}, Arrays.asList(-5, 7), 1.0);
        check(
                new int[]{Integer.MIN_VALUE, Integer.MIN_VALUE, Integer.MAX_VALUE, Integer.MAX_VALUE},
                Arrays.asList(Integer.MIN_VALUE, Integer.MAX_VALUE),
                -0.5
        );
        check(new int[]{3, 1, 2}, Arrays.asList(1, 2, 3), 2.0);

        exhaustive(8, new int[]{-1, 0, 1});

        boolean nullThrown = false;
        boolean emptyThrown = false;
        try { ModeMedian.solve(null); } catch (IllegalArgumentException e) { nullThrown = true; }
        try { ModeMedian.solve(new int[0]); } catch (IllegalArgumentException e) { emptyThrown = true; }
        if (!nullThrown || !emptyThrown) {
            throw new AssertionError("invalid input must be rejected");
        }

        System.out.println("PASS fixed=5 exhaustive=9840 invalid-input=2 overflow-safe-even-median=true");
    }
}
