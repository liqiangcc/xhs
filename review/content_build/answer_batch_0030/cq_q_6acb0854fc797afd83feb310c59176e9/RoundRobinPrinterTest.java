import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public final class RoundRobinPrinterTest {
    private record Event(int workerId, int value) {}

    public static void main(String[] args) throws Exception {
        for (int i = 0; i < 100; i++) {
            verifyRound(2, 10);
            verifyRound(3, 10);
        }
        verifyRound(4, 1);
        verifyRound(2, 0);
        verifyInvalidArguments();
        System.out.println("PASS rounds=202 exact-sequence=yes round-robin-ownership=yes no-duplicates=yes termination=yes invalid-args=yes");
    }

    private static void verifyRound(int workers, int max) throws Exception {
        RoundRobinPrinter printer = new RoundRobinPrinter(workers, max);
        CopyOnWriteArrayList<Event> events = new CopyOnWriteArrayList<>();
        CountDownLatch start = new CountDownLatch(1);
        List<Thread> threads = new ArrayList<>();
        for (int workerId = 0; workerId < workers; workerId++) {
            final int id = workerId;
            Thread thread = new Thread(() -> {
                try {
                    start.await();
                    printer.runWorker(id, (owner, value) -> events.add(new Event(owner, value)));
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException(e);
                }
            }, "printer-" + workerId);
            threads.add(thread);
            thread.start();
        }
        start.countDown();
        for (Thread thread : threads) {
            thread.join(TimeUnit.SECONDS.toMillis(2));
            if (thread.isAlive()) {
                throw new AssertionError("worker did not terminate: " + thread.getName());
            }
        }
        if (events.size() != max) {
            throw new AssertionError("expected " + max + " events, got " + events.size());
        }
        for (int index = 0; index < max; index++) {
            Event event = events.get(index);
            int expectedValue = index + 1;
            int expectedWorker = index % workers;
            if (event.value() != expectedValue) {
                throw new AssertionError("sequence mismatch at " + index + ": " + event);
            }
            if (event.workerId() != expectedWorker) {
                throw new AssertionError("owner mismatch at " + index + ": " + event);
            }
        }
    }

    private static void verifyInvalidArguments() {
        assertThrows(() -> new RoundRobinPrinter(1, 10));
        assertThrows(() -> new RoundRobinPrinter(2, -1));
        RoundRobinPrinter printer = new RoundRobinPrinter(2, 1);
        assertThrows(() -> {
            try {
                printer.runWorker(2, (worker, value) -> {});
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });
    }

    private static void assertThrows(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }
}
