import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public final class MinPowerOfTwoOperationsTest {
    private static final Map<Long, Integer> ORACLE_MEMO = new HashMap<>();

    static {
        ORACLE_MEMO.put(0L, 0);
        ORACLE_MEMO.put(1L, 1);
    }

    public static void main(String[] args) {
        int fixed = runFixedCases();
        int randomized = runRandomizedDifferential();
        System.out.printf(
                "PASS fixed=%d randomized=%d oracle=two-branch-signed-digit-dp%n",
                fixed,
                randomized);
    }

    private static int runFixedCases() {
        int[] values = {
            0,
            1,
            -1,
            2,
            -2,
            3,
            -3,
            4,
            5,
            6,
            7,
            8,
            15,
            16,
            31,
            Integer.MAX_VALUE,
            Integer.MIN_VALUE,
            42
        };
        int[] expected = {
            0,
            1,
            1,
            1,
            1,
            2,
            2,
            1,
            2,
            2,
            2,
            1,
            2,
            1,
            2,
            2,
            1,
            3
        };

        for (int i = 0; i < values.length; i++) {
            int actual = MinPowerOfTwoOperations.minOperations(values[i]);
            if (actual != expected[i]) {
                throw new AssertionError(
                        "fixed case value=" + values[i]
                                + " expected=" + expected[i]
                                + " actual=" + actual);
            }
            int oracle = exactOracle(Math.abs((long) values[i]));
            if (actual != oracle) {
                throw new AssertionError(
                        "fixed oracle mismatch value=" + values[i]
                                + " oracle=" + oracle
                                + " actual=" + actual);
            }
        }
        return values.length;
    }

    private static int runRandomizedDifferential() {
        Random random = new Random(20260823L);
        int checks = 20_000;
        for (int i = 0; i < checks; i++) {
            int value = random.nextInt();
            int actual = MinPowerOfTwoOperations.minOperations(value);
            int expected = exactOracle(Math.abs((long) value));
            if (actual != expected) {
                throw new AssertionError(
                        "random mismatch value=" + value
                                + " expected=" + expected
                                + " actual=" + actual);
            }
        }
        return checks;
    }

    private static int exactOracle(long value) {
        Integer cached = ORACLE_MEMO.get(value);
        if (cached != null) {
            return cached;
        }

        int result;
        if ((value & 1L) == 0L) {
            result = exactOracle(value >> 1);
        } else {
            int subtractLowBit = exactOracle((value - 1L) >> 1);
            int addLowBit = exactOracle((value + 1L) >> 1);
            result = 1 + Math.min(subtractLowBit, addLowBit);
        }
        ORACLE_MEMO.put(value, result);
        return result;
    }
}
