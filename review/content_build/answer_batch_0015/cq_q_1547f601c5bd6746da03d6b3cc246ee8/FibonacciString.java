import java.math.BigInteger;
import java.util.Objects;

public final class FibonacciString {
    private FibonacciString() {}

    public static boolean canSplitIntoFibonacci(String digits) {
        Objects.requireNonNull(digits, "digits");
        for (int i = 0; i < digits.length(); i++) {
            char ch = digits.charAt(i);
            if (ch < '1' || ch > '9') {
                throw new IllegalArgumentException("expected digits 1-9 only");
            }
        }
        if (digits.length() < 3) return false;

        int length = digits.length();
        for (int firstEnd = 1; firstEnd <= length - 2; firstEnd++) {
            BigInteger first = new BigInteger(digits.substring(0, firstEnd));
            for (int secondEnd = firstEnd + 1; secondEnd <= length - 1; secondEnd++) {
                BigInteger second = new BigInteger(digits.substring(firstEnd, secondEnd));
                if (matchesForcedSuffix(digits, secondEnd, first, second)) {
                    return true;
                }
            }
        }
        return false;
    }

    private static boolean matchesForcedSuffix(
        String digits,
        int index,
        BigInteger first,
        BigInteger second
    ) {
        int terms = 2;
        while (index < digits.length()) {
            BigInteger sum = first.add(second);
            String expected = sum.toString();
            if (!digits.startsWith(expected, index)) return false;
            index += expected.length();
            first = second;
            second = sum;
            terms++;
        }
        return terms >= 3;
    }
}
