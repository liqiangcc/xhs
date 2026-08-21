import java.math.BigInteger;
import java.util.Random;

public final class DecimalStringMultiplierTest {
    private static final long SEED = 43L;

    public static void main(String[] args) {
        int boundaryCases = 0;
        boundaryCases += assertProduct("2", "3", "6");
        boundaryCases += assertProduct("123", "456", "56088");
        boundaryCases += assertProduct("0", "999999", "0");
        boundaryCases += assertProduct("0000", "000123", "0");
        boundaryCases += assertProduct("00012", "003", "36");
        boundaryCases += assertProduct("99999", "99999", "9999800001");
        boundaryCases += assertProduct("1", "98765432101234567890", "98765432101234567890");

        assertInvalid(null, "1");
        assertInvalid("", "1");
        assertInvalid("12a", "3");
        assertInvalid("-12", "3");

        Random random = new Random(SEED);
        int randomCases = 5000;
        for (int i = 0; i < randomCases; i++) {
            String left = randomDecimal(random, 1 + random.nextInt(80));
            String right = randomDecimal(random, 1 + random.nextInt(80));
            String expected = new BigInteger(left).multiply(new BigInteger(right)).toString();
            String actual = DecimalStringMultiplier.multiply(left, right);
            if (!expected.equals(actual)) {
                throw new AssertionError("mismatch left=" + left + " right=" + right
                        + " expected=" + expected + " actual=" + actual);
            }
        }

        System.out.println("PASS random_cases=" + randomCases
                + " seed=" + SEED
                + " official_examples=2"
                + " boundary_cases=" + boundaryCases
                + " invalid_input_cases=4");
    }

    private static int assertProduct(String left, String right, String expected) {
        String actual = DecimalStringMultiplier.multiply(left, right);
        if (!expected.equals(actual)) {
            throw new AssertionError(left + " * " + right + " expected=" + expected + " actual=" + actual);
        }
        return 1;
    }

    private static void assertInvalid(String left, String right) {
        try {
            DecimalStringMultiplier.multiply(left, right);
            throw new AssertionError("expected IllegalArgumentException for left=" + left + " right=" + right);
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    private static String randomDecimal(Random random, int length) {
        StringBuilder value = new StringBuilder(length);
        value.append((char) ('1' + random.nextInt(9)));
        for (int i = 1; i < length; i++) {
            value.append((char) ('0' + random.nextInt(10)));
        }
        return value.toString();
    }
}
