import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Objects;
import java.util.function.LongSupplier;

public final class SlidingWindowRateLimiter {
    private final int maxCalls;
    private final long windowMillis;
    private final LongSupplier clock;
    private final Deque<Long> accepted = new ArrayDeque<>();
    private long lastNow = -1L;

    public SlidingWindowRateLimiter(int maxCalls, long windowMillis, LongSupplier clock) {
        if (maxCalls <= 0) throw new IllegalArgumentException("maxCalls must be > 0");
        if (windowMillis <= 0) throw new IllegalArgumentException("windowMillis must be > 0");
        this.maxCalls = maxCalls;
        this.windowMillis = windowMillis;
        this.clock = Objects.requireNonNull(clock, "clock");
    }

    public boolean allow() {
        long now = clock.getAsLong();
        if (now < 0) throw new IllegalStateException("clock must be non-negative");
        if (lastNow >= 0 && now < lastNow) {
            throw new IllegalStateException("clock must be non-decreasing");
        }
        lastNow = now;

        long cutoff = now >= windowMillis ? now - windowMillis : -1L;
        while (!accepted.isEmpty() && accepted.peekFirst() <= cutoff) {
            accepted.removeFirst();
        }
        if (accepted.size() >= maxCalls) {
            return false;
        }
        accepted.addLast(now);
        return true;
    }
}
