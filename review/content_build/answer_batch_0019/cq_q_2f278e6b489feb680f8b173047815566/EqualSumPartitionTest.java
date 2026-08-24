import java.util.Arrays;
import java.util.Random;

public final class EqualSumPartitionTest {
    private static int fixed = 0;
    private static int randomized = 0;

    public static void main(String[] args) {
        fixedCases();
        randomizedDifferential();
        System.out.println("PASS fixed=" + fixed
            + " randomized=" + randomized
            + " oracle=exhaustive-subset-partition mutation=none");
    }

    private static void fixedCases() {
        expect(false, EqualSumPartition.canPartition(null), "null");
        fixed++;

        int[] empty = {};
        expectWithMutationCheck(empty, true, "empty");
        fixed++;

        int[] one = {1};
        expectWithMutationCheck(one, false, "single odd");
        fixed++;

        int[] zero = {0};
        expectWithMutationCheck(zero, true, "single zero under empty-group candidate contract");
        fixed++;

        int[] classicTrue = {1, 5, 11, 5};
        expectWithMutationCheck(classicTrue, true, "classic true");
        fixed++;

        int[] classicFalse = {1, 2, 3, 5};
        expectWithMutationCheck(classicFalse, false, "odd total");
        fixed++;

        int[] evenImpossible = {2, 2, 3, 5};
        expectWithMutationCheck(evenImpossible, false, "even total but unreachable half");
        fixed++;

        int[] duplicates = {2, 2, 2, 2};
        expectWithMutationCheck(duplicates, true, "duplicates");
        fixed++;

        int[] zerosAndValues = {0, 0, 3, 3};
        expectWithMutationCheck(zerosAndValues, true, "zeros plus values");
        fixed++;

        expectThrows(new int[] {-1, 1}, "negative element rejected by candidate contract");
        fixed++;
    }

    private static void randomizedDifferential() {
        Random random = new Random(0x5eed0019L);
        for (int i = 0; i < 5000; i++) {
            int n = random.nextInt(13); // exhaustive oracle: at most 4096 masks
            int[] values = new int[n];
            for (int j = 0; j < n; j++) {
                values[j] = random.nextInt(21);
            }
            int[] before = values.clone();
            boolean actual = EqualSumPartition.canPartition(values);
            boolean expected = oracle(values);
            if (actual != expected) {
                throw new AssertionError("random mismatch values=" + Arrays.toString(values)
                    + " expected=" + expected + " actual=" + actual);
            }
            if (!Arrays.equals(before, values)) {
                throw new AssertionError("input mutated values=" + Arrays.toString(values));
            }
            randomized++;
        }
    }

    private static boolean oracle(int[] values) {
        long total = 0L;
        for (int value : values) {
            total += value;
        }
        if ((total & 1L) != 0L) {
            return false;
        }
        long target = total / 2L;
        int masks = 1 << values.length;
        for (int mask = 0; mask < masks; mask++) {
            long sum = 0L;
            for (int i = 0; i < values.length; i++) {
                if ((mask & (1 << i)) != 0) {
                    sum += values[i];
                }
            }
            if (sum == target) {
                return true;
            }
        }
        return false;
    }

    private static void expectWithMutationCheck(int[] input, boolean expected, String label) {
        int[] before = input.clone();
        expect(expected, EqualSumPartition.canPartition(input), label);
        if (!Arrays.equals(before, input)) {
            throw new AssertionError(label + ": input mutated");
        }
    }

    private static void expectThrows(int[] input, String label) {
        int[] before = input.clone();
        try {
            EqualSumPartition.canPartition(input);
            throw new AssertionError(label + ": expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            if (!Arrays.equals(before, input)) {
                throw new AssertionError(label + ": input mutated");
            }
        }
    }

    private static void expect(boolean expected, boolean actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
    }
}
