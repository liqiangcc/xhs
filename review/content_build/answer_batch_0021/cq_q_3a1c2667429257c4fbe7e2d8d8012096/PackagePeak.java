import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class PackagePeak {
    private PackagePeak() {}

    public record Interval(long putTime, long takeTime) {}
    public record Segment(long start, long end) {}
    public record Result(long maxPackages, List<Segment> segments, long totalPeakDuration) {}

    public static Result findPeak(List<Interval> intervals) {
        if (intervals == null) throw new IllegalArgumentException("intervals is null");
        long eventCount = Math.multiplyExact((long) intervals.size(), 2L);
        if (eventCount > Integer.MAX_VALUE) throw new IllegalArgumentException("too many intervals for one Java array");
        long[] events = new long[(int) eventCount];
        int p = 0;
        for (Interval x : intervals) {
            if (x == null || x.putTime() < 0 || x.takeTime() <= x.putTime()
                    || x.takeTime() > (Long.MAX_VALUE >>> 1)) {
                throw new IllegalArgumentException("invalid interval");
            }
            events[p++] = (x.putTime() << 1) | 1L;
            events[p++] = (x.takeTime() << 1);
        }
        Arrays.sort(events);

        long current = 0;
        long max = 0;
        long total = 0;
        ArrayList<Segment> peaks = new ArrayList<>();
        int i = 0;
        while (i < events.length) {
            long t = events[i] >>> 1;
            long delta = 0;
            while (i < events.length && (events[i] >>> 1) == t) {
                delta += ((events[i] & 1L) == 1L) ? 1L : -1L;
                i++;
            }
            current += delta;
            if (current < 0) throw new IllegalStateException("negative active package count");
            if (i == events.length) break;
            long next = events[i] >>> 1;
            if (next <= t || current <= 0) continue;
            if (current > max) {
                max = current;
                peaks.clear();
                total = 0;
            }
            if (current == max) {
                total = Math.addExact(total, next - t);
                if (!peaks.isEmpty() && peaks.get(peaks.size() - 1).end() == t) {
                    Segment last = peaks.remove(peaks.size() - 1);
                    peaks.add(new Segment(last.start(), next));
                } else {
                    peaks.add(new Segment(t, next));
                }
            }
        }
        return new Result(max, List.copyOf(peaks), total);
    }
}
