import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicStampedReference;

public final class CasExamples {
    public static final class LockedCasInt {
        private int value;
        public LockedCasInt(int initial) { value = initial; }
        public synchronized int get() { return value; }
        public synchronized boolean compareAndSet(int expected, int update) {
            if (value != expected) return false;
            value = update;
            return true;
        }
    }

    public static int incrementAndGet(AtomicInteger value) {
        for (;;) {
            int current = value.get();
            int next = Math.incrementExact(current);
            if (value.compareAndSet(current, next)) return next;
        }
    }

    public static boolean staleStampRejectedAfterAba() {
        Object a = new Object();
        Object b = new Object();
        AtomicStampedReference<Object> ref = new AtomicStampedReference<>(a, 0);
        int staleStamp = ref.getStamp();
        if (!ref.compareAndSet(a, b, 0, 1)) throw new AssertionError("A->B failed");
        if (!ref.compareAndSet(b, a, 1, 2)) throw new AssertionError("B->A failed");
        return !ref.compareAndSet(a, new Object(), staleStamp, staleStamp + 1);
    }
}
