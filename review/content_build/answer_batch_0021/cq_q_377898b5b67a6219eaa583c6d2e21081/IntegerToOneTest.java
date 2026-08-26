import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public final class IntegerToOneTest {
    private static final Map<Long, Integer> MEMO = new HashMap<>();
    static { MEMO.put(1L, 0); }

    private static int exact(long n) {
        Integer cached = MEMO.get(n);
        if (cached != null) return cached;
        final int result;
        if ((n & 1L) == 0L) {
            result = 1 + exact(n >>> 1);
        } else {
            // One +/- operation followed by the forced division by two.
            result = 2 + Math.min(exact(n >>> 1), exact((n >>> 1) + 1L));
        }
        MEMO.put(n, result);
        return result;
    }

    private static void check(int n) {
        int actual = IntegerToOne.minOperations(n);
        int expected = exact(n);
        if (actual != expected) {
            throw new AssertionError("n=" + n + " actual=" + actual + " expected=" + expected);
        }
    }

    public static void main(String[] args) {
        int[][] fixed = {
            {1,0},{2,1},{3,2},{4,2},{7,4},{8,3},{15,5},{31,6},{123456789,37},{Integer.MAX_VALUE,32}
        };
        for (int[] row : fixed) {
            int actual = IntegerToOne.minOperations(row[0]);
            if (actual != row[1]) throw new AssertionError("fixed n=" + row[0] + " got=" + actual);
            check(row[0]);
        }
        for (int n = 1; n <= 200_000; n++) check(n);
        Random random = new Random(20260826L);
        for (int i = 0; i < 50_000; i++) check(1 + random.nextInt(Integer.MAX_VALUE));
        try {
            IntegerToOne.minOperations(0);
            throw new AssertionError("zero must be rejected");
        } catch (IllegalArgumentException expected) {}
        try {
            IntegerToOne.minOperations(-1);
            throw new AssertionError("negative must be rejected");
        } catch (IllegalArgumentException expected) {}
        System.out.println("PASS fixed=10 exhaustive=200000 randomized=50000 oracle=exact-recurrence int-max=32 invalid=reject");
    }
}
