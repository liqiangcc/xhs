import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;

public final class StringAdditionTest {
    private static void require(String actual, String expected, String name) {
        if (!actual.equals(expected)) throw new AssertionError(name + ": expected " + expected + ", got " + actual);
    }

    private static void requireIllegal(String first, String second) {
        try {
            StringAddition.add(first, second);
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    private static List<String> smallDecimals() {
        List<String> values = new ArrayList<>();
        for (int length = 1; length <= 3; length++) {
            int count = 1;
            for (int i = 0; i < length; i++) count *= 4;
            for (int encoded = 0; encoded < count; encoded++) {
                int value = encoded;
                char[] chars = new char[length];
                for (int i = length - 1; i >= 0; i--) { chars[i] = (char) ('0' + value % 4); value /= 4; }
                values.add(new String(chars));
            }
        }
        return values;
    }

    private static void exhaustiveBigIntegerOracle() {
        List<String> values = smallDecimals();
        for (String first : values) for (String second : values) {
            String expected = new BigInteger(first).add(new BigInteger(second)).toString();
            require(StringAddition.add(first, second), expected, "oracle " + first + "+" + second);
        }
    }

    public static void main(String[] args) {
        require(StringAddition.add("0", "0"), "0", "zero");
        require(StringAddition.add("9", "1"), "10", "final carry");
        require(StringAddition.add("999", "1"), "1000", "carry chain");
        require(StringAddition.add("000", "000"), "0", "normalized zero");
        require(StringAddition.add("00099", "001"), "100", "leading zero input");
        require(StringAddition.add("123456789012345678901234567890", "987654321098765432109876543210"), "1111111110111111111011111111100", "beyond long");
        requireIllegal(null, "1"); requireIllegal("", "1"); requireIllegal("1a", "2"); requireIllegal("-1", "2");
        exhaustiveBigIntegerOracle();
    }
}
