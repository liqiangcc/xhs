import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class PackagePeakWriterTest {
    private static long randomizedCases;

    public static void main(String[] args) {
        assertResult(List.of(), new PackagePeak.Result(0, List.of(), 0));
        assertResult(List.of(new PackagePeak.Interval(0, 10), new PackagePeak.Interval(10, 20)),
                new PackagePeak.Result(1, List.of(new PackagePeak.Segment(0, 20)), 20));
        assertResult(List.of(new PackagePeak.Interval(0, 5), new PackagePeak.Interval(2, 3),
                             new PackagePeak.Interval(7, 9), new PackagePeak.Interval(8, 10)),
                new PackagePeak.Result(2, List.of(new PackagePeak.Segment(2, 3), new PackagePeak.Segment(8, 9)), 2));
        assertResult(List.of(new PackagePeak.Interval(10_000_000_000L, 10_000_000_100L),
                             new PackagePeak.Interval(10_000_000_020L, 10_000_000_050L)),
                new PackagePeak.Result(2, List.of(new PackagePeak.Segment(10_000_000_020L, 10_000_000_050L)), 30));

        Random rnd = new Random(0x21_3A1C266L);
        for (int c = 0; c < 12_000; c++) {
            int horizon = 2 + rnd.nextInt(15);
            int n = rnd.nextInt(24);
            ArrayList<PackagePeak.Interval> xs = new ArrayList<>();
            for (int j = 0; j < n; j++) {
                int a = rnd.nextInt(horizon);
                int b = a + 1 + rnd.nextInt(horizon - a);
                xs.add(new PackagePeak.Interval(a, b));
            }
            PackagePeak.Result actual = PackagePeak.findPeak(xs);
            PackagePeak.Result expected = brute(xs, horizon);
            if (!actual.equals(expected)) {
                throw new AssertionError("random mismatch case=" + c + " intervals=" + xs + " actual=" + actual + " expected=" + expected);
            }
            randomizedCases++;
        }

        expectInvalid(List.of(new PackagePeak.Interval(5, 5)));
        expectInvalid(List.of(new PackagePeak.Interval(5, 4)));
        expectInvalid(List.of(new PackagePeak.Interval(-1, 4)));
        System.out.printf("PASS randomized_cases=%d simultaneous_boundary=pass disjoint_peaks=pass large_timestamp=pass invalid_contract=pass%n", randomizedCases);
    }

    private static PackagePeak.Result brute(List<PackagePeak.Interval> xs, int horizon) {
        long max = 0;
        long[] count = new long[horizon];
        for (PackagePeak.Interval x : xs) {
            for (int t = (int) x.putTime(); t < (int) x.takeTime(); t++) count[t]++;
        }
        for (long v : count) max = Math.max(max, v);
        if (max == 0) return new PackagePeak.Result(0, List.of(), 0);
        ArrayList<PackagePeak.Segment> out = new ArrayList<>();
        long total = 0;
        int t = 0;
        while (t < horizon) {
            if (count[t] != max) { t++; continue; }
            int start = t;
            while (t < horizon && count[t] == max) t++;
            out.add(new PackagePeak.Segment(start, t));
            total += t - start;
        }
        return new PackagePeak.Result(max, List.copyOf(out), total);
    }

    private static void assertResult(List<PackagePeak.Interval> xs, PackagePeak.Result expected) {
        PackagePeak.Result actual = PackagePeak.findPeak(xs);
        if (!actual.equals(expected)) throw new AssertionError("actual=" + actual + " expected=" + expected);
    }

    private static void expectInvalid(List<PackagePeak.Interval> xs) {
        try {
            PackagePeak.findPeak(xs);
            throw new AssertionError("expected invalid interval");
        } catch (IllegalArgumentException expected) {
            // pass
        }
    }
}
