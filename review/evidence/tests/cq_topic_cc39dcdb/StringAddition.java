public final class StringAddition {
    private StringAddition() {}

    public static String add(String first, String second) {
        validate(first);
        validate(second);
        int i = first.length() - 1, j = second.length() - 1, carry = 0;
        StringBuilder reversed = new StringBuilder(Math.max(first.length(), second.length()) + 1);
        while (i >= 0 || j >= 0 || carry != 0) {
            int left = i >= 0 ? first.charAt(i--) - '0' : 0;
            int right = j >= 0 ? second.charAt(j--) - '0' : 0;
            int sum = left + right + carry;
            reversed.append((char) ('0' + sum % 10));
            carry = sum / 10;
        }
        return trimLeadingZeros(reversed.reverse().toString());
    }

    private static void validate(String value) {
        if (value == null || value.isEmpty()) throw new IllegalArgumentException("non-empty decimal string required");
        for (int i = 0; i < value.length(); i++) {
            if (value.charAt(i) < '0' || value.charAt(i) > '9') {
                throw new IllegalArgumentException("decimal digits only");
            }
        }
    }

    private static String trimLeadingZeros(String value) {
        int firstNonZero = 0;
        while (firstNonZero < value.length() - 1 && value.charAt(firstNonZero) == '0') firstNonZero++;
        return value.substring(firstNonZero);
    }
}
