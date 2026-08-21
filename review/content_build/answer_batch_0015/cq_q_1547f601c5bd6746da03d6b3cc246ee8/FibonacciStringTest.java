import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class FibonacciStringTest {
    private static void assertValue(String input, boolean expected) {
        boolean actual = FibonacciString.canSplitIntoFibonacci(input);
        if (actual != expected) {
            throw new AssertionError("input=" + input + " expected=" + expected + " actual=" + actual);
        }
    }

    private static boolean bruteForceOracle(String digits) {
        return enumerate(digits, 0, new ArrayList<>());
    }

    private static boolean enumerate(String digits, int index, List<BigInteger> values) {
        if (index == digits.length()) return values.size() >= 3;

        for (int end = index + 1; end <= digits.length(); end++) {
            BigInteger value = new BigInteger(digits.substring(index, end));
            int size = values.size();
            if (size >= 2) {
                BigInteger expected = values.get(size - 2).add(values.get(size - 1));
                int comparison = value.compareTo(expected);
                if (comparison > 0) break;
                if (comparison < 0) continue;
            }

            values.add(value);
            if (enumerate(digits, end, values)) return true;
            values.remove(values.size() - 1);
        }
        return false;
    }

    private static String randomDigits(Random random, int length) {
        StringBuilder builder = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            builder.append((char) ('1' + random.nextInt(9)));
        }
        return builder.toString();
    }

    public static void main(String[] args) {
        assertValue("112", true);           // 1,1,2
        assertValue("123", true);           // 1,2,3
        assertValue("11235813", true);      // 1,1,2,3,5,8,13
        assertValue("12122436", true);      // 12,12,24,36
        assertValue("1234", false);         // 1,2,3 leaves 4; no full split works
        assertValue("999", false);
        assertValue("11", false);

        String huge = "1111111111111111111111111111111111111111";
        assertValue(huge + huge + "2222222222222222222222222222222222222222", true);

        boolean nullRejected = false;
        try {
            FibonacciString.canSplitIntoFibonacci(null);
        } catch (NullPointerException expected) {
            nullRejected = true;
        }
        if (!nullRejected) throw new AssertionError("null must be rejected by candidate contract");

        boolean zeroRejected = false;
        try {
            FibonacciString.canSplitIntoFibonacci("1102");
        } catch (IllegalArgumentException expected) {
            zeroRejected = true;
        }
        if (!zeroRejected) throw new AssertionError("digits outside 1-9 must be rejected");

        Random random = new Random(0x1547f601L);
        int randomized = 5000;
        for (int round = 0; round < randomized; round++) {
            int length = 3 + random.nextInt(10);
            String input = randomDigits(random, length);
            boolean expected = bruteForceOracle(input);
            boolean actual = FibonacciString.canSplitIntoFibonacci(input);
            if (actual != expected) {
                throw new AssertionError(
                    "random input=" + input + " expected=" + expected + " actual=" + actual
                );
            }
        }

        System.out.println(
            "PASS fixed=8 randomized=" + randomized
                + " oracle=recursive-all-partitions big_integer=true full_consumption=true"
        );
    }
}
