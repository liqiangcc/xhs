public final class FileSizeEstimateTest {
    private static void eq(long actual, long expected, String name) {
        if (actual != expected) throw new AssertionError(name + ": " + actual + " != " + expected);
    }
    public static void main(String[] args) {
        long n=20_000_000L;
        eq(FileSizeEstimate.estimateHomogeneous(n,5,1,1),120_000_000L,"ascii-lf");
        eq(FileSizeEstimate.estimateHomogeneous(n,5,1,2),140_000_000L,"ascii-crlf");
        eq(FileSizeEstimate.estimateHomogeneous(n,5,3,1),320_000_000L,"three-byte-lf");
        eq(FileSizeEstimate.estimateHomogeneous(n,5,3,2),340_000_000L,"three-byte-crlf");
        eq(FileSizeEstimate.estimateHomogeneous(0,5,1,1),0L,"zero-lines");
        boolean neg=false; try { FileSizeEstimate.estimateHomogeneous(-1,5,1,1); } catch (IllegalArgumentException e) { neg=true; }
        if (!neg) throw new AssertionError("negative input must fail");
        boolean overflow=false; try { FileSizeEstimate.estimateHomogeneous(Long.MAX_VALUE,5,4,2); } catch (ArithmeticException e) { overflow=true; }
        if (!overflow) throw new AssertionError("overflow must fail");
        System.out.println("PASS ascii-lf=120000000 ascii-crlf=140000000 three-byte-lf=320000000 three-byte-crlf=340000000 zero=0 negative=rejected overflow=rejected");
    }
}
