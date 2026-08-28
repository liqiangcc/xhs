public final class Utf8TextSizeTest {
    private static void expect(long expected, long actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    private static void expectInvalid(String record, String newline, long lines) {
        try {
            Utf8TextSize.logicalBytes(record, newline, lines);
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    public static void main(String[] args) {
        long lines = 20_000_000L;
        expect(120_000_000L, Utf8TextSize.logicalBytes("abcde", "\n", lines), "ascii-lf");
        expect(320_000_000L, Utf8TextSize.logicalBytes("你好世界啊", "\n", lines), "cjk-lf");
        expect(420_000_000L, Utf8TextSize.logicalBytes("😀😀😀😀😀", "\n", lines), "four-byte-lf");
        expect(140_000_000L, Utf8TextSize.logicalBytes("abcde", "\r\n", lines), "ascii-crlf");
        expectInvalid("abcd", "\n", lines);
        expectInvalid("abcde", "\n", -1);
        System.out.println("PASS ascii-lf=120000000 cjk-lf=320000000 four-byte-lf=420000000 ascii-crlf=140000000 invalid=rejected");
    }
}
