import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

public class writer_validation {
    static final class AlternatingPrinter {
        private final Object monitor = new Object();
        private final int maxInclusive;
        private int next = 0;

        AlternatingPrinter(int maxInclusive) {
            if (maxInclusive < 0) throw new IllegalArgumentException("maxInclusive must be >= 0");
            this.maxInclusive = maxInclusive;
        }

        void printEven() throws InterruptedException { printParity(0); }
        void printOdd() throws InterruptedException { printParity(1); }

        private void printParity(int parity) throws InterruptedException {
            while (true) {
                synchronized (monitor) {
                    while (next <= maxInclusive && (next & 1) != parity) {
                        monitor.wait();
                    }
                    if (next > maxInclusive) {
                        monitor.notifyAll();
                        return;
                    }
                    System.out.println(next);
                    next++;
                    monitor.notifyAll();
                }
            }
        }
    }

    static void check(int max, boolean oddStartsFirst) throws Exception {
        PrintStream original = System.out;
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        PrintStream capture = new PrintStream(bytes, true, StandardCharsets.UTF_8);
        AtomicReference<Throwable> failure = new AtomicReference<>();
        try {
            System.setOut(capture);
            AlternatingPrinter printer = new AlternatingPrinter(max);
            Thread even = new Thread(() -> {
                try { printer.printEven(); } catch (Throwable t) { failure.compareAndSet(null, t); }
            }, "even");
            Thread odd = new Thread(() -> {
                try { printer.printOdd(); } catch (Throwable t) { failure.compareAndSet(null, t); }
            }, "odd");
            if (oddStartsFirst) {
                odd.start();
                Thread.yield();
                even.start();
            } else {
                even.start();
                Thread.yield();
                odd.start();
            }
            even.join(3000);
            odd.join(3000);
            if (even.isAlive() || odd.isAlive()) {
                even.interrupt(); odd.interrupt();
                throw new AssertionError("threads failed to terminate for max=" + max);
            }
            if (failure.get() != null) throw new AssertionError("thread failure", failure.get());
        } finally {
            capture.flush();
            System.setOut(original);
        }

        String text = bytes.toString(StandardCharsets.UTF_8).trim();
        List<Integer> got = new ArrayList<>();
        if (!text.isEmpty()) {
            for (String line : text.split("\\R")) got.add(Integer.parseInt(line.trim()));
        }
        if (got.size() != max + 1) throw new AssertionError("count mismatch max=" + max + " got=" + got.size());
        for (int i = 0; i <= max; i++) {
            if (got.get(i) != i) throw new AssertionError("order mismatch max=" + max + " at=" + i + " got=" + got.get(i));
        }
    }

    public static void main(String[] args) throws Exception {
        boolean rejected = false;
        try { new AlternatingPrinter(-1); } catch (IllegalArgumentException expected) { rejected = true; }
        if (!rejected) throw new AssertionError("negative max must be rejected");

        int deterministic = 0;
        for (int max : new int[]{0, 1, 2, 3, 10, 31, 100}) {
            check(max, false); deterministic++;
            check(max, true); deterministic++;
        }

        Random random = new Random(20260826L);
        int randomized = 0;
        for (int i = 0; i < 1000; i++) {
            int max = random.nextInt(201);
            check(max, random.nextBoolean());
            randomized++;
        }

        System.out.println("PASS negative=rejected deterministic=" + deterministic
                + " randomized=" + randomized
                + " exact_order=0..max termination=verified odd-first=verified even-first=verified");
    }
}
