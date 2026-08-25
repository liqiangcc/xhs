import java.util.function.LongSupplier;

public final class SlidingWindowRateLimiterTest {
    static final class FakeClock implements LongSupplier {
        long now;
        FakeClock(long initial) { now = initial; }
        void set(long value) { now = value; }
        @Override public long getAsLong() { return now; }
    }
    static void expect(boolean actual, boolean expected, String name) {
        if (actual != expected) throw new AssertionError(name + ": expected=" + expected + " actual=" + actual);
    }
    static void expectThrows(Runnable r, String name) {
        try { r.run(); } catch (RuntimeException expected) { return; }
        throw new AssertionError(name + ": expected exception");
    }
    public static void main(String[] args) {
        FakeClock c = new FakeClock(0);
        SlidingWindowRateLimiter limiter = new SlidingWindowRateLimiter(3, 1000, c);
        expect(limiter.allow(), true, "t0");
        c.set(100); expect(limiter.allow(), true, "t100");
        c.set(200); expect(limiter.allow(), true, "t200");
        c.set(300); expect(limiter.allow(), false, "t300-over-limit");
        c.set(999); expect(limiter.allow(), false, "t999-rejected-attempt-not-counted");
        c.set(1000); expect(limiter.allow(), true, "exact-boundary-expires-t0");
        c.set(1001); expect(limiter.allow(), false, "still-three-accepted");
        c.set(1100); expect(limiter.allow(), true, "exact-boundary-expires-t100");

        FakeClock burstClock = new FakeClock(42);
        SlidingWindowRateLimiter burst = new SlidingWindowRateLimiter(2, 10, burstClock);
        expect(burst.allow(), true, "burst-1");
        expect(burst.allow(), true, "burst-2");
        expect(burst.allow(), false, "burst-3");
        burstClock.set(52); expect(burst.allow(), true, "burst-expired-at-boundary");

        FakeClock reg = new FakeClock(5);
        SlidingWindowRateLimiter regLimiter = new SlidingWindowRateLimiter(1, 10, reg);
        expect(regLimiter.allow(), true, "reg-first");
        reg.set(4); expectThrows(regLimiter::allow, "clock-regression");
        expectThrows(() -> new SlidingWindowRateLimiter(0, 1, () -> 0L), "bad-limit");
        expectThrows(() -> new SlidingWindowRateLimiter(1, 0, () -> 0L), "bad-window");
        SlidingWindowRateLimiter neg = new SlidingWindowRateLimiter(1, 1, () -> -1L);
        expectThrows(neg::allow, "negative-clock");
        System.out.println("PASS sliding-window accepted-only exact-boundary burst regression invalid-config");
    }
}
