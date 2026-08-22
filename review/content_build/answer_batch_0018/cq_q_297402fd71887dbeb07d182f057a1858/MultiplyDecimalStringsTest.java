import java.math.BigInteger;
import java.util.Random;

public final class MultiplyDecimalStringsTest {
    private static int fixedChecks;

    public static void main(String[] args) {
        expect("0", "0", "0");
        expect("0000", "12345", "0");
        expect("1", "999999999999", "999999999999");
        expect("9", "9", "81");
        expect("123", "456", "56088");
        expect("999", "999", "998001");
        expect("123456789", "987654321", "121932631112635269");
        expectInvalid(null, "1");
        expectInvalid("1", null);
        expectInvalid("", "1");
        expectInvalid("1", "");
        expectInvalid("-1", "2");
        expectInvalid("1.5", "2");
        expectInvalid("12a3", "2");

        Random random = new Random(20260823L);
        int randomized = 4000;
        for (int i = 0; i < randomized; i++) {
  String left = randomDigits(random, 1 + random.nextInt(80));
  String right = randomDigits(random, 1 + random.nextInt(80));
  String expected = new BigInteger(left).multiply(new BigInteger(right)).toString();
  String actual = MultiplyDecimalStrings.multiply(left, right);
  if (!expected.equals(actual)) {
      throw new AssertionError("oracle mismatch: " + left + " * " + right
              + " expected=" + expected + " actual=" + actual);
  }
  String reversed = MultiplyDecimalStrings.multiply(right, left);
  if (!actual.equals(reversed)) {
      throw new AssertionError("commutativity mismatch: " + left + " * " + right);
  }
        }
        System.out.println("PASS fixed=" + fixedChecks
      + " randomized=" + randomized
      + " oracle=BigInteger commutative=true");
    }

    private static void expect(String left, String right, String expected) {
        fixedChecks++;
        String actual = MultiplyDecimalStrings.multiply(left, right);
        if (!expected.equals(actual)) {
  throw new AssertionError(left + " * " + right + ": expected "
          + expected + " but got " + actual);
        }
    }

    private static void expectInvalid(String left, String right) {
        fixedChecks++;
        try {
  MultiplyDecimalStrings.multiply(left, right);
  throw new AssertionError("expected IllegalArgumentException for left=" + left
          + " right=" + right);
        } catch (IllegalArgumentException expected) {
  // expected
        }
    }

    private static String randomDigits(Random random, int length) {
        StringBuilder out = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
  out.append((char) ('0' + random.nextInt(10)));
        }
        return out.toString();
    }
}
