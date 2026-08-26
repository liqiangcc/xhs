import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

public final class CasExamplesTest {
    public static void main(String[] args) throws Exception {
        CasExamples.LockedCasInt locked = new CasExamples.LockedCasInt(10);
        if (!locked.compareAndSet(10, 11) || locked.get() != 11) throw new AssertionError("semantic CAS success");
        if (locked.compareAndSet(10, 99) || locked.get() != 11) throw new AssertionError("stale expected must fail without write");

        AtomicInteger counter = new AtomicInteger();
        int threads = 8, each = 20_000;
        CountDownLatch start = new CountDownLatch(1);
        List<Thread> workers = new ArrayList<>();
        for (int t = 0; t < threads; t++) {
            Thread worker = new Thread(() -> {
                try { start.await(); } catch (InterruptedException e) { throw new RuntimeException(e); }
                for (int i = 0; i < each; i++) CasExamples.incrementAndGet(counter);
            });
            workers.add(worker); worker.start();
        }
        start.countDown();
        for (Thread worker : workers) worker.join();
        if (counter.get() != threads * each) throw new AssertionError("lost update: " + counter.get());

        AtomicInteger stale = new AtomicInteger(5);
        int observed = stale.get();
        if (!stale.compareAndSet(5, 6)) throw new AssertionError("competing update");
        if (stale.compareAndSet(observed, 7)) throw new AssertionError("stale expected should fail");
        if (stale.get() != 6) throw new AssertionError("failed CAS modified state");

        if (!CasExamples.staleStampRejectedAfterAba()) throw new AssertionError("stale stamp should detect A-B-A");

        AtomicInteger max = new AtomicInteger(Integer.MAX_VALUE);
        try {
            CasExamples.incrementAndGet(max);
            throw new AssertionError("expected overflow");
        } catch (ArithmeticException expected) {
            if (max.get() != Integer.MAX_VALUE) throw new AssertionError("overflow changed state");
        }
        System.out.println("PASS locked-semantic-cas stale-expected concurrent-cas-loop no-lost-update stamped-aba-detection overflow-fail-closed");
    }
}
