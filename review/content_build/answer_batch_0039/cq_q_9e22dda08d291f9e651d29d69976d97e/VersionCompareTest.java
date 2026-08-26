public final class VersionCompareTest {
    private static void expect(int expected, String left, String right) {
        int actual = VersionCompare.compareVersion(left, right);
        if (actual != expected) {
            throw new AssertionError(left + " vs " + right + ": expected " + expected + " but got " + actual);
        }
    }

    private static void expectReject(String value) {
        try {
            VersionCompare.compareVersion(value, "1.0");
            throw new AssertionError("expected rejection for: " + value);
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    public static void main(String[] args) {
        expect(0, "1.0", "1");
        expect(0, "1.01", "1.001");
        expect(1, "1.0.1", "1");
        expect(1, "1.10", "1.2");
        expect(-1, "0.1", "1.1");
        expect(1, "2147483648", "2147483647");
        expect(0, "0000000000000000000000001.0.0", "1");
        expect(1, "99999999999999999999999999999999999999", "10000000000000000000000000000000000000");
        expectReject("1..0");
        expectReject("1.0-alpha");
        try {
            VersionCompare.compareVersion(null, "1");
            throw new AssertionError("expected null rejection");
        } catch (IllegalArgumentException expected) {
            // expected
        }
        System.out.println("PASS equal-trailing-zero leading-zero ordering arbitrary-length invalid-contract");
    }
}
