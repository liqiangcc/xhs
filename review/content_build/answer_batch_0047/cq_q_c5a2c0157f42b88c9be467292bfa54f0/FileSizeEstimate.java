public final class FileSizeEstimate {
    public static long estimateHomogeneous(
            long lines, int charsPerLine, int bytesPerCharacter, int newlineBytes) {
        if (lines < 0 || charsPerLine < 0 || bytesPerCharacter < 0 || newlineBytes < 0) {
            throw new IllegalArgumentException("sizes must be non-negative");
        }
        long body = Math.multiplyExact((long) charsPerLine, bytesPerCharacter);
        long bytesPerLine = Math.addExact(body, newlineBytes);
        return Math.multiplyExact(lines, bytesPerLine);
    }
}
