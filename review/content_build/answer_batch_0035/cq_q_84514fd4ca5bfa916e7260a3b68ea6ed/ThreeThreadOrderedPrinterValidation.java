import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.BiConsumer;

public final class ThreeThreadOrderedPrinterValidation {
    static final class ThreeThreadOrderedPrinter {
        private final ReentrantLock lock = new ReentrantLock();
        private final Condition[] turns = {
                lock.newCondition(), lock.newCondition(), lock.newCondition()
        };
        private final int limit;
        private final BiConsumer<Integer, Integer> output;
        private int next = 1;
        private boolean cancelled;

        ThreeThreadOrderedPrinter(int limit, BiConsumer<Integer, Integer> output) {
            this.limit = limit;
            this.output = output;
        }

        void runWorker(int workerId) {
            lock.lock();
            try {
                while (true) {
                    while (!cancelled && next <= limit && owner(next) != workerId) {
                        turns[workerId].await();
                    }
                    if (cancelled || next > limit) {
                        signalAllTurns();
                        return;
                    }
                    int value = next++;
                    try {
                        output.accept(workerId, value);
                    } catch (RuntimeException | Error e) {
                        cancelled = true;
                        signalAllTurns();
                        throw e;
                    }
                    if (next <= limit) {
                        turns[owner(next)].signal();
                    } else {
                        signalAllTurns();
                    }
                }
            } catch (InterruptedException e) {
                cancelled = true;
                signalAllTurns();
                Thread.currentThread().interrupt();
            } finally {
                lock.unlock();
            }
        }

        private void signalAllTurns() {
            for (Condition turn : turns) {
                turn.signalAll();
            }
        }

        private static int owner(int value) {
            return Math.floorMod(value - 1, 3);
        }
    }

    record Event(int worker, int value) {}

    static void joinAll(Thread[] threads) throws Exception {
        for (Thread thread : threads) thread.join(3000);
        for (Thread thread : threads) {
            if (thread.isAlive()) throw new AssertionError("thread still alive: " + thread.getName());
        }
    }

    static void normal(int limit, int seed) throws Exception {
        List<Event> events = Collections.synchronizedList(new ArrayList<>());
        var printer = new ThreeThreadOrderedPrinter(limit, (worker, value) -> events.add(new Event(worker, value)));
        Thread[] threads = new Thread[3];
        for (int i = 0; i < 3; i++) {
            final int id = i;
            threads[i] = new Thread(() -> printer.runWorker(id), "worker-" + id);
        }
        List<Thread> order = new ArrayList<>(Arrays.asList(threads));
        Collections.shuffle(order, new Random(seed));
        for (Thread thread : order) thread.start();
        joinAll(threads);
        if (events.size() != Math.max(limit, 0)) throw new AssertionError("size=" + events.size() + " limit=" + limit);
        for (int i = 0; i < events.size(); i++) {
            Event event = events.get(i);
            int value = i + 1;
            if (event.value() != value || event.worker() != (value - 1) % 3) {
                throw new AssertionError("bad event index=" + i + " event=" + event);
            }
        }
    }

    static void interruptCancellation() throws Exception {
        List<Event> events = Collections.synchronizedList(new ArrayList<>());
        var printer = new ThreeThreadOrderedPrinter(100, (worker, value) -> events.add(new Event(worker, value)));
        Thread worker1 = new Thread(() -> printer.runWorker(1), "interrupt-target");
        worker1.start();
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
        while (worker1.getState() != Thread.State.WAITING && System.nanoTime() < deadline) Thread.onSpinWait();
        if (worker1.getState() != Thread.State.WAITING) throw new AssertionError("worker1 did not await");
        worker1.interrupt();
        worker1.join(2000);
        if (worker1.isAlive()) throw new AssertionError("interrupted worker stuck");
        Thread worker0 = new Thread(() -> printer.runWorker(0), "worker-0-after-cancel");
        Thread worker2 = new Thread(() -> printer.runWorker(2), "worker-2-after-cancel");
        worker0.start();
        worker2.start();
        joinAll(new Thread[]{worker0, worker2});
        if (!events.isEmpty()) throw new AssertionError("output after cancellation: " + events);
        if (!worker1.isInterrupted()) throw new AssertionError("interrupt flag not restored");
    }

    static void outputFailureCancellation() throws Exception {
        AtomicReference<Throwable> failure = new AtomicReference<>();
        List<Event> events = Collections.synchronizedList(new ArrayList<>());
        var printer = new ThreeThreadOrderedPrinter(100, (worker, value) -> {
            events.add(new Event(worker, value));
            if (value == 2) throw new IllegalStateException("boom");
        });
        Thread[] threads = new Thread[3];
        for (int i = 0; i < 3; i++) {
            final int id = i;
            threads[i] = new Thread(() -> {
                try {
                    printer.runWorker(id);
                } catch (Throwable t) {
                    failure.compareAndSet(null, t);
                }
            }, "failure-worker-" + id);
        }
        for (Thread thread : threads) thread.start();
        joinAll(threads);
        if (!(failure.get() instanceof IllegalStateException)) throw new AssertionError("failure not propagated: " + failure.get());
        if (events.size() != 2 || events.get(0).value() != 1 || events.get(1).value() != 2) {
            throw new AssertionError("unexpected output before failure: " + events);
        }
    }

    public static void main(String[] args) throws Exception {
        normal(0, 0);
        normal(1, 1);
        normal(2, 2);
        normal(3, 3);
        normal(9, 4);
        for (int i = 0; i < 200; i++) normal(1 + (i * 37) % 211, 1000 + i);
        interruptCancellation();
        outputFailureCancellation();
        System.out.println("PASS fixed=5 stress=200 randomized-start=true exact-order=true owner-partition=true interrupt-cancel=true output-failure-cancel=true timeout-clean=true");
    }
}
