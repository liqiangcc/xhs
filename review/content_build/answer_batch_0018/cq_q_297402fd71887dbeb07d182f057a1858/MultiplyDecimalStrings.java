public final class MultiplyDecimalStrings {
    private MultiplyDecimalStrings() {}

    public static String multiply(String left, String right) {
        requireDigits(left, "left");
        requireDigits(right, "right");

        int m = left.length();
        int n = right.length();
        long[] digits = new long[m + n];

        for (int i = 0; i < m; i++) {
            int a = left.charAt(i) - '0';
            for (int j = 0; j < n; j++) {
                int b = right.charAt(j) - '0';
                digits[i + j + 1] += (long) a * b;
            }
        }

        for (int k = digits.length - 1; k > 0; k--) {
            digits[k - 1] += digits[k] / 10;
            digits[k] %= 10;
        }

        int first = 0;
        while (first < digits.length - 1 && digits[first] == 0) {
            first++;
        }
        StringBuilder out = new StringBuilder(digits.length - first);
        for (int i = first; i < digits.length; i++) {
            out.append((char) ('0' + digits[i]));
        }
        return out.toString();
    }

    private static void requireDigits(String value, String name) {
        if (value == null || value.isEmpty()) {
            throw new IllegalArgumentException(name + " must be a non-empty decimal string");
        }
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c < '0' || c > '9') {
                throw new IllegalArgumentException(name + " must contain only decimal digits");
            }
        }
    }
}
