import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

public final class HorseRaceFixture {
    static final int HORSES = 10;

    static final class Outcome {
        final List<Integer> order;
        final List<String> events;
        Outcome(List<Integer> order, List<String> events) {
            this.order = order;
            this.events = events;
        }
    }

    static Outcome race(boolean failOne) throws Exception {
        CountDownLatch ready = new CountDownLatch(HORSES);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch finish = new CountDownLatch(HORSES);
        ConcurrentLinkedQueue<Integer> order = new ConcurrentLinkedQueue<>();
        ConcurrentLinkedQueue<String> events = new ConcurrentLinkedQueue<>();
        AtomicReference<Throwable> failure = new AtomicReference<>();
        AtomicBoolean announced = new AtomicBoolean(false);
        AtomicInteger started = new AtomicInteger();
        List<Thread> threads = new ArrayList<>();

        for (int i = 0; i < HORSES; i++) {
            final int id = i;
            Thread t = new Thread(() -> {
                events.add("ready:" + id);
                ready.countDown();
                try {
                    start.await();
                    events.add("start:" + id);
                    started.incrementAndGet();
                    if (failOne && id == 3) throw new IllegalStateException("simulated failure");
                    // Deterministic stagger: all threads have crossed the start gate before this work matters.
                    Thread.sleep((HORSES - id) * 2L);
                    order.add(id);
                    events.add("finish:" + id);
                } catch (InterruptedException e) {
                    failure.compareAndSet(null, e);
                    Thread.currentThread().interrupt();
                } catch (Throwable t1) {
                    failure.compareAndSet(null, t1);
                    events.add("failed:" + id);
                } finally {
                    finish.countDown();
                }
            }, "horse-" + id);
            threads.add(t);
            t.start();
        }

        if (!ready.await(5, TimeUnit.SECONDS)) throw new AssertionError("ready timeout");
        events.add("go");
        start.countDown();
        if (!finish.await(5, TimeUnit.SECONDS)) throw new AssertionError("finish timeout");
        events.add("announce");
        announced.set(true);
        for (Thread t : threads) t.join(1000);
        if (!announced.get()) throw new AssertionError("announce missing");
        if (failOne && failure.get() == null) throw new AssertionError("failure not captured");
        return new Outcome(List.copyOf(order), List.copyOf(events));
    }

    static void assertNormalRound(Outcome o) {
        int go = o.events.indexOf("go");
        int announce = o.events.indexOf("announce");
        if (go < 0 || announce < 0 || go >= announce) throw new AssertionError(o.events);
        Set<Integer> readyIds = new HashSet<>();
        Set<Integer> startIds = new HashSet<>();
        Set<Integer> finishIds = new HashSet<>();
        for (int i = 0; i < o.events.size(); i++) {
            String e = o.events.get(i);
            if (e.startsWith("ready:")) {
                if (i > go) throw new AssertionError("ready after go: " + o.events);
                readyIds.add(Integer.parseInt(e.substring(6)));
            } else if (e.startsWith("start:")) {
                if (i < go) throw new AssertionError("start before go: " + o.events);
                startIds.add(Integer.parseInt(e.substring(6)));
            } else if (e.startsWith("finish:")) {
                if (i > announce) throw new AssertionError("finish after announce: " + o.events);
                finishIds.add(Integer.parseInt(e.substring(7)));
            }
        }
        if (readyIds.size() != HORSES || startIds.size() != HORSES || finishIds.size() != HORSES) throw new AssertionError(o.events);
        if (o.order.size() != HORSES || new HashSet<>(o.order).size() != HORSES) throw new AssertionError(o.order);
    }

    static void assertFailureRound(Outcome o) {
        int announce = o.events.indexOf("announce");
        if (announce < 0) throw new AssertionError("referee did not terminate after horse failure");
        long ready = o.events.stream().filter(s -> s.startsWith("ready:")).count();
        long starts = o.events.stream().filter(s -> s.startsWith("start:")).count();
        long failures = o.events.stream().filter(s -> s.equals("failed:3")).count();
        if (ready != HORSES || starts != HORSES || failures != 1) throw new AssertionError(o.events);
    }

    public static void main(String[] args) throws Exception {
        for (int round = 0; round < 60; round++) assertNormalRound(race(false));
        assertFailureRound(race(true));
        System.out.println("PASS rounds=60 all-ready-before-go all-start-after-go all-finish-before-announce unique-results=10 failure-does-not-deadlock");
    }
}
