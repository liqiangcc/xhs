import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

class writer_validation {
    static final class DclSingleton {
        private static volatile DclSingleton instance;
        private static final AtomicInteger constructions = new AtomicInteger();
        final int initialized;

        private DclSingleton() {
            initialized = 42;
            constructions.incrementAndGet();
        }

        static DclSingleton getInstance() {
            DclSingleton local = instance;
            if (local == null) {
                synchronized (DclSingleton.class) {
                    local = instance;
                    if (local == null) {
                        local = new DclSingleton();
                        instance = local;
                    }
                }
            }
            return local;
        }
    }

    public static void main(String[] args) throws Exception {
        Field f = DclSingleton.class.getDeclaredField("instance");
        if (!Modifier.isStatic(f.getModifiers()) || !Modifier.isVolatile(f.getModifiers())) {
            throw new AssertionError("instance must be static volatile");
        }

        int threads = 128;
        int callsPerThread = 2000;
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        CyclicBarrier barrier = new CyclicBarrier(threads);
        ConcurrentLinkedQueue<DclSingleton> seen = new ConcurrentLinkedQueue<>();
        List<Future<?>> futures = new ArrayList<>();
        for (int t = 0; t < threads; t++) {
            futures.add(pool.submit(() -> {
                barrier.await();
                DclSingleton first = null;
                for (int i = 0; i < callsPerThread; i++) {
                    DclSingleton s = DclSingleton.getInstance();
                    if (s.initialized != 42) throw new AssertionError("not initialized");
                    if (first == null) first = s;
                    else if (first != s) throw new AssertionError("thread observed multiple identities");
                }
                seen.add(first);
                return null;
            }));
        }
        for (Future<?> x : futures) x.get();
        pool.shutdown();
        if (!pool.awaitTermination(30, TimeUnit.SECONDS)) throw new AssertionError("pool did not terminate");
        DclSingleton expected = seen.peek();
        for (DclSingleton s : seen) if (s != expected) throw new AssertionError("cross-thread identity mismatch");
        if (DclSingleton.constructions.get() != 1) throw new AssertionError("constructed " + DclSingleton.constructions.get());
        if (DclSingleton.getInstance() != expected) throw new AssertionError("stable fast path identity");
        System.out.println("PASS volatile=reflected threads=" + threads + " callsPerThread=" + callsPerThread + " constructions=1 identity=stable initialized=42");
    }
}
