import java.util.concurrent.Semaphore;

public final class RoundRobinABC {
    private RoundRobinABC() {}

    public static String print(int rounds) throws InterruptedException {
        if (rounds < 0) throw new IllegalArgumentException("rounds must be nonnegative");

        Semaphore a = new Semaphore(1);
        Semaphore b = new Semaphore(0);
        Semaphore c = new Semaphore(0);
        StringBuilder output = new StringBuilder();

        Thread ta = worker('A', rounds, a, b, output);
        Thread tb = worker('B', rounds, b, c, output);
        Thread tc = worker('C', rounds, c, a, output);
        Thread[] threads = {ta, tb, tc};

        for (Thread thread : threads) thread.start();
        try {
            for (Thread thread : threads) thread.join();
        } catch (InterruptedException e) {
            for (Thread thread : threads) thread.interrupt();
            throw e;
        }
        return output.toString();
    }

    private static Thread worker(
            char value,
            int rounds,
            Semaphore mine,
            Semaphore next,
            StringBuilder output) {
        return new Thread(() -> {
            for (int i = 0; i < rounds; i++) {
                try {
                    mine.acquire();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                output.append(value);
                next.release();
            }
        }, "printer-" + value);
    }
}
