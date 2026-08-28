public final class BigNumberAdditionTest {
    private static void expect(String expected, String actual, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    private static void expectInvalid(String a, String b, String label) {
        try {
            BigNumberAddition.addNonNegativeDecimalStrings(a, b);
            throw new AssertionError(label + " expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    public static void main(String[] args) {
        expect("0", BigNumberAddition.addNonNegativeDecimalStrings("0", "0"), "zero");
        expect("1000", BigNumberAddition.addNonNegativeDecimalStrings("999", "1"), "carry chain");
        expect("1000000000000000000000000000000",
                BigNumberAddition.addNonNegativeDecimalStrings(
                        "999999999999999999999999999999", "1"),
                "beyond long");
        expect("579", BigNumberAddition.addNonNegativeDecimalStrings("123", "456"), "same length");
        expect("1005", BigNumberAddition.addNonNegativeDecimalStrings("5", "1000"), "unequal length");
        expect("12", BigNumberAddition.addNonNegativeDecimalStrings("0007", "0005"), "leading zeros");
        expectInvalid("", "1", "empty");
        expectInvalid("-1", "1", "negative");
        expectInvalid("1.0", "2", "decimal point");
        expectInvalid("12x", "3", "nondigit");
        System.out.println(
                "PASS zero=0 carry=1000 beyond-long=ok unequal=1005 leading-zero=12 invalid-input=rejected");
    }
}
