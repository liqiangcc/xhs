import java.math.BigInteger;
import java.util.Random;

public final class LinkedListBigIntegerAddTest {
    private static int fixed = 0;
    private static int randomized = 0;

    public static void main(String[] args) {
        check("0", "0");
        check("9", "1");
        check("123", "456");
        check("999", "1");
        check("1000", "999");
        check("1", "999999999999999999999999999999");
        check("314159265358979323846", "271828182845904523536");
        check("99999999999999999999", "99999999999999999999");
        fixed = 8;

        Random random = new Random(0x10B16CCCL);
        for (int i = 0; i < 5000; i++) {
            String left = randomNumber(random, 1 + random.nextInt(80));
            String right = randomNumber(random, 1 + random.nextInt(80));
            check(left, right);
            randomized++;
        }

        expectNullFailure();
        expectInvalidDigitFailure();
        System.out.println(
                "PASS fixed=" + fixed
                        + " randomized=" + randomized
                        + " oracle=java.math.BigInteger"
                        + " input_immutable=true null=fail-fast invalid_digit=fail-fast");
    }

    private static void check(String leftText, String rightText) {
        LinkedListBigIntegerAdd.ListNode left = fromDigits(leftText);
        LinkedListBigIntegerAdd.ListNode right = fromDigits(rightText);
        String leftBefore = digits(left);
        String rightBefore = digits(right);

        LinkedListBigIntegerAdd.ListNode actual = LinkedListBigIntegerAdd.add(left, right);
        String actualText = digits(actual);
        String expected = new BigInteger(leftText).add(new BigInteger(rightText)).toString();

        if (!expected.equals(actualText)) {
            throw new AssertionError(
                    "left=" + leftText
                            + " right=" + rightText
                            + " expected=" + expected
                            + " actual=" + actualText);
        }
        if (!leftBefore.equals(digits(left)) || !rightBefore.equals(digits(right))) {
            throw new AssertionError("input list was mutated");
        }
    }

    private static String randomNumber(Random random, int length) {
        StringBuilder builder = new StringBuilder(length);
        if (length == 1) {
            builder.append((char) ('0' + random.nextInt(10)));
            return builder.toString();
        }
        builder.append((char) ('1' + random.nextInt(9)));
        for (int i = 1; i < length; i++) {
            builder.append((char) ('0' + random.nextInt(10)));
        }
        return builder.toString();
    }

    private static LinkedListBigIntegerAdd.ListNode fromDigits(String digits) {
        LinkedListBigIntegerAdd.ListNode head = null;
        LinkedListBigIntegerAdd.ListNode tail = null;
        for (int i = 0; i < digits.length(); i++) {
            LinkedListBigIntegerAdd.ListNode node =
                    new LinkedListBigIntegerAdd.ListNode(digits.charAt(i) - '0');
            if (head == null) {
                head = node;
            } else {
                tail.next = node;
            }
            tail = node;
        }
        return head;
    }

    private static String digits(LinkedListBigIntegerAdd.ListNode head) {
        StringBuilder builder = new StringBuilder();
        for (LinkedListBigIntegerAdd.ListNode node = head; node != null; node = node.next) {
            builder.append((char) ('0' + node.digit));
        }
        return builder.toString();
    }

    private static void expectNullFailure() {
        LinkedListBigIntegerAdd.ListNode one = new LinkedListBigIntegerAdd.ListNode(1);
        try {
            LinkedListBigIntegerAdd.add(null, one);
            throw new AssertionError("expected NullPointerException for null left");
        } catch (NullPointerException expected) {
            // explicit candidate API contract
        }
        try {
            LinkedListBigIntegerAdd.add(one, null);
            throw new AssertionError("expected NullPointerException for null right");
        } catch (NullPointerException expected) {
            // explicit candidate API contract
        }
    }

    private static void expectInvalidDigitFailure() {
        try {
            new LinkedListBigIntegerAdd.ListNode(10);
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // explicit candidate API contract
        }
    }
}
