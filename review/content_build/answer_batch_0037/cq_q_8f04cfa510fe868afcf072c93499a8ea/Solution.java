import java.util.concurrent.Semaphore;

public final class Solution {
    public String withSemaphores(int pairs) throws InterruptedException {
        if (pairs < 0) throw new IllegalArgumentException("pairs must be >= 0");
        StringBuilder out = new StringBuilder(pairs * 2);
        Semaphore aPermit = new Semaphore(1);
        Semaphore bPermit = new Semaphore(0);

        Thread a = new Thread(() -> {
            try {
                for (int i = 0; i < pairs; i++) {
                    aPermit.acquire();
                    out.append('a');
                    bPermit.release();
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "print-a");

        Thread b = new Thread(() -> {
            try {
                for (int i = 0; i < pairs; i++) {
                    bPermit.acquire();
                    out.append('b');
                    aPermit.release();
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "print-b");

        b.start();
        a.start();
        a.join();
        b.join();
        return out.toString();
    }

    public String withWaitNotify(int pairs) throws InterruptedException {
        if (pairs < 0) throw new IllegalArgumentException("pairs must be >= 0");
        Object lock = new Object();
        boolean[] aTurn = {true};
        StringBuilder out = new StringBuilder(pairs * 2);

        Thread a = new Thread(() -> runWithMonitor(lock, aTurn, true, 'a', pairs, out), "print-a");
        Thread b = new Thread(() -> runWithMonitor(lock, aTurn, false, 'b', pairs, out), "print-b");

        b.start();
        a.start();
        a.join();
        b.join();
        return out.toString();
    }

    private void runWithMonitor(Object lock, boolean[] aTurn, boolean myTurn,
                                char ch, int pairs, StringBuilder out) {
        try {
            for (int i = 0; i < pairs; i++) {
                synchronized (lock) {
                    while (aTurn[0] != myTurn) {
                        lock.wait();
                    }
                    out.append(ch);
                    aTurn[0] = !aTurn[0];
                    lock.notifyAll();
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
