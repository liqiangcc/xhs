public final class DecimalStringMultiplier {
    private DecimalStringMultiplier() {}

    public static String multiply(String num1, String num2) {
        String a = normalize(num1, "num1");
        String b = normalize(num2, "num2");
        if (a.equals("0") || b.equals("0")) {
            return "0";
        }

        int m = a.length();
        int n = b.length();
        long[] acc = new long[m + n];

        for (int i = m - 1; i >= 0; i--) {
            int digitA = a.charAt(i) - '0';
            for (int j = n - 1; j >= 0; j--) {
                int digitB = b.charAt(j) - '0';
                acc[i + j + 1] += (long) digitA * digitB;
            }
        }

        for (int pos = acc.length - 1; pos > 0; pos--) {
            acc[pos - 1] += acc[pos] / 10;
            acc[pos] %= 10;
        }

        StringBuilder product = new StringBuilder(acc.length);
        int start = acc[0] == 0 ? 1 : 0;
        for (int i = start; i < acc.length; i++) {
            product.append((char) ('0' + acc[i]));
        }
        return product.length() == 0 ? "0" : product.toString();
    }

    private static String normalize(String value, String name) {
        if (value == null || value.isEmpty()) {
            throw new IllegalArgumentException(name + " must be a non-empty decimal string");
        }
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch < '0' || ch > '9') {
                throw new IllegalArgumentException(name + " must contain decimal digits only");
            }
        }
        int firstNonZero = 0;
        while (firstNonZero < value.length() - 1 && value.charAt(firstNonZero) == '0') {
            firstNonZero++;
        }
        return value.substring(firstNonZero);
    }
}
