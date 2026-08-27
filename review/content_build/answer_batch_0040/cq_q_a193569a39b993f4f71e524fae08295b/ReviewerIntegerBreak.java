public final class ReviewerIntegerBreak {
    private static long compositionOracle(int n) {
        int gaps = n - 1;
        long best = Long.MIN_VALUE;
        int limit = 1 << gaps;
        for (int mask = 1; mask < limit; mask++) {
            int part = 1;
            long product = 1;
            for (int g = 0; g < gaps; g++) {
                if ((mask & (1 << g)) != 0) {
                    product *= part;
                    part = 1;
                } else {
                    part++;
                }
            }
            product *= part;
            if (product > best) best = product;
        }
        return best;
    }

    private static long theoremOracle(int n) {
        if (n == 2) return 1;
        if (n == 3) return 2;
        long p = 1;
        while (n > 4) { p *= 3; n -= 3; }
        return p * n;
    }

    public static void main(String[] args) {
        for (int n = 2; n <= 18; n++) {
            long expected = compositionOracle(n);
            long actual = IntegerBreak.solve(n);
            if (actual != expected) throw new AssertionError("composition mismatch n=" + n + " expected=" + expected + " actual=" + actual);
        }
        for (int n = 2; n <= 53; n++) {
            long expected = theoremOracle(n);
            long actual = IntegerBreak.solve(n);
            if (actual != expected) throw new AssertionError("range mismatch n=" + n + " expected=" + expected + " actual=" + actual);
        }
        if (IntegerBreak.solve(2) != 1 || IntegerBreak.solve(3) != 2 || IntegerBreak.solve(10) != 36 || IntegerBreak.solve(53) != 258_280_326L) throw new AssertionError("boundary/example mismatch");
        System.out.println("PASS compositions-n=2..18 theorem-n=2..53 boundaries=1,2,36,258280326");
    }
}
