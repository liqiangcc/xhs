import java.util.Random;

public final class RotateStringTest {
    private static int fixed = 0;
    private static int randomized = 0;

    public static void main(String[] args) {
        check("abcde", "cdeab");
        check("abcde", "abced");
        check("a", "a");
        check("a", "b");
        check("aaaa", "aaaa");
        check("aaab", "abaa");
        check("waterbottle", "erbottlewat");
        check("", "");
        check("abc", "ab");
        check("abab", "baba");
        fixed = 10;

        Random random = new Random(0x0E622220L);
        for (int t = 0; t < 5000; t++) {
            int n = random.nextInt(31);
            String s = randomString(random, n);
            String goal;
            if (n > 0 && t % 2 == 0) {
                int shift = random.nextInt(n);
                goal = s.substring(shift) + s.substring(0, shift);
            } else {
                int goalLength = (t % 7 == 0) ? random.nextInt(31) : n;
                goal = randomString(random, goalLength);
            }
            check(s, goal);
            randomized++;
        }

        expectNullFailure();
        System.out.println(
                "PASS fixed=" + fixed
                        + " randomized=" + randomized
                        + " oracle=enumerate-rotations"
                        + " empty=true null=fail-fast");
    }

    private static String randomString(Random random, int length) {
        StringBuilder builder = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            builder.append((char) ('a' + random.nextInt(4)));
        }
        return builder.toString();
    }

    private static void check(String s, String goal) {
        boolean expected = oracle(s, goal);
        boolean actual = RotateString.rotateString(s, goal);
        if (expected != actual) {
            throw new AssertionError(
                    "s=" + s + " goal=" + goal
                            + " expected=" + expected
                            + " actual=" + actual);
        }
    }

    private static boolean oracle(String s, String goal) {
        if (s.length() != goal.length()) {
            return false;
        }
        int n = s.length();
        if (n == 0) {
            return true;
        }
        for (int shift = 0; shift < n; shift++) {
            boolean same = true;
            for (int i = 0; i < n; i++) {
                if (goal.charAt(i) != s.charAt((i + shift) % n)) {
                    same = false;
                    break;
                }
            }
            if (same) {
                return true;
            }
        }
        return false;
    }

    private static void expectNullFailure() {
        try {
            RotateString.rotateString(null, "a");
            throw new AssertionError("expected NullPointerException for null s");
        } catch (NullPointerException expected) {
            // explicit implementation contract
        }
        try {
            RotateString.rotateString("a", null);
            throw new AssertionError("expected NullPointerException for null goal");
        } catch (NullPointerException expected) {
            // explicit implementation contract
        }
    }
}
