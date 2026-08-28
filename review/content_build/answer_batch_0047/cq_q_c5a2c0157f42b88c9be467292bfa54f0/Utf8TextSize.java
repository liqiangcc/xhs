import java.nio.charset.StandardCharsets;

public final class Utf8TextSize {
    public static long logicalBytes(
            String fiveCodePointRecord,
            String lineEnding,
            long lines) {
        if (fiveCodePointRecord == null || lineEnding == null || lines < 0) {
            throw new IllegalArgumentException("invalid input");
        }
        if (fiveCodePointRecord.codePointCount(0, fiveCodePointRecord.length()) != 5) {
            throw new IllegalArgumentException("record must contain exactly 5 Unicode code points");
        }

        long recordBytes =
                fiveCodePointRecord.getBytes(StandardCharsets.UTF_8).length;
        long newlineBytes =
                lineEnding.getBytes(StandardCharsets.UTF_8).length;
        return Math.multiplyExact(lines, recordBytes + newlineBytes);
    }
}
