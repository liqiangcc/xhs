public final class BigNumberAddition {
    public static String addNonNegativeDecimalStrings(String a, String b) {
        validateDecimal(a);
        validateDecimal(b);

        int i = a.length() - 1;
        int j = b.length() - 1;
        int carry = 0;
        StringBuilder reversed =
                new StringBuilder(Math.max(a.length(), b.length()) + 1);

        while (i >= 0 || j >= 0 || carry != 0) {
            int da = i >= 0 ? a.charAt(i--) - '0' : 0;
            int db = j >= 0 ? b.charAt(j--) - '0' : 0;
            int sum = da + db + carry;
            reversed.append((char) ('0' + sum % 10));
            carry = sum / 10;
        }

        reversed.reverse();
        int firstNonZero = 0;
        while (firstNonZero < reversed.length() - 1
                && reversed.charAt(firstNonZero) == '0') {
            firstNonZero++;
        }
        return reversed.substring(firstNonZero);
    }

    private static void validateDecimal(String value) {
        if (value == null || value.isEmpty()) {
            throw new IllegalArgumentException("decimal string must be non-empty");
        }
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c < '0' || c > '9') {
                throw new IllegalArgumentException(
                        "decimal string must contain only digits");
            }
        }
    }
}
