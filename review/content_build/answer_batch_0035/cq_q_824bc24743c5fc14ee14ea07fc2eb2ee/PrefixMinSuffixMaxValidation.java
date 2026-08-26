import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class PrefixMinSuffixMaxValidation {
    static List<Integer> findSpecial(int[] a) {
        List<Integer> result = new ArrayList<>();
        if (a == null || a.length < 3) return result;
        int n = a.length;
        int[] suffixMax = new int[n];
        suffixMax[n - 1] = a[n - 1];
        for (int i = n - 2; i >= 0; i--) suffixMax[i] = Math.max(a[i], suffixMax[i + 1]);
        int prefixMin = a[0];
        for (int i = 1; i <= n - 2; i++) {
            if (a[i] < prefixMin && a[i] > suffixMax[i + 1]) result.add(a[i]);
            prefixMin = Math.min(prefixMin, a[i]);
        }
        return result;
    }

    static List<Integer> brute(int[] a) {
        List<Integer> out = new ArrayList<>();
        if (a == null || a.length < 3) return out;
        for (int i = 1; i <= a.length - 2; i++) {
            boolean smallerThanAllBefore = true;
            boolean largerThanAllAfter = true;
            for (int j = 0; j < i; j++) if (!(a[i] < a[j])) smallerThanAllBefore = false;
            for (int j = i + 1; j < a.length; j++) if (!(a[i] > a[j])) largerThanAllAfter = false;
            if (smallerThanAllBefore && largerThanAllAfter) out.add(a[i]);
        }
        return out;
    }

    static void expect(int[] input, Integer... expected) {
        List<Integer> actual = findSpecial(input);
        if (!actual.equals(Arrays.asList(expected))) {
            throw new AssertionError("input=" + Arrays.toString(input) + " expected=" + Arrays.asList(expected) + " actual=" + actual);
        }
        if (!actual.equals(brute(input))) throw new AssertionError("oracle mismatch for " + Arrays.toString(input));
    }

    public static void main(String[] args) {
        expect(new int[]{9,8,7,6,5}, 8,7,6);
        expect(new int[]{9,8,8,7});
        expect(new int[]{10,5,9,4,3}, 4);
        expect(new int[]{1,2});
        expect(new int[]{3,2,1}, 2);
        expect(new int[]{3,1,2});

        Random random = new Random(82424743L);
        int randomCases = 5000;
        for (int t = 0; t < randomCases; t++) {
            int n = random.nextInt(18);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = random.nextInt(21) - 10;
            List<Integer> fast = findSpecial(a);
            List<Integer> slow = brute(a);
            if (!fast.equals(slow)) {
                throw new AssertionError("random oracle mismatch input=" + Arrays.toString(a) + " fast=" + fast + " slow=" + slow);
            }
        }
        System.out.println("PASS fixed=6 randomized=5000 oracle=quadratic-strict endpoints=excluded duplicates=strict");
    }
}
