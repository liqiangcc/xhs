import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

public final class DeadlockCase {
    private static final ReentrantLock LOCK_A = new ReentrantLock();
    private static final ReentrantLock LOCK_B = new ReentrantLock();
    private static final CountDownLatch BOTH_HOLD_ONE = new CountDownLatch(2);

    private static void await(CountDownLatch latch) {
        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        }
    }

    private static Thread worker(
            String name, ReentrantLock first, ReentrantLock second) {
        Thread t = new Thread(() -> {
            first.lock();
            try {
                BOTH_HOLD_ONE.countDown();
                await(BOTH_HOLD_ONE);
                second.lock();
                try {
                    // 永远到不了这里：另一个线程正持有 second 并等待 first。
                } finally {
                    second.unlock();
                }
            } finally {
                first.unlock();
            }
        }, name);
        // 演示线程设为 daemon，检测到死锁后 JVM 仍能退出，不让示例/CI 永久挂住。
        t.setDaemon(true);
        return t;
    }

    public static void main(String[] args) throws Exception {
        Thread t1 = worker("A-then-B", LOCK_A, LOCK_B);
        Thread t2 = worker("B-then-A", LOCK_B, LOCK_A);
        t1.start();
        t2.start();

        ThreadMXBean bean = ManagementFactory.getThreadMXBean();
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(3);
        while (System.nanoTime() < deadline) {
            long[] ids = bean.findDeadlockedThreads();
            if (ids != null && ids.length >= 2) {
                System.out.println("DEADLOCK_DETECTED threads=" + ids.length);
                return;
            }
            Thread.sleep(10);
        }
        throw new AssertionError("deadlock was not detected within deadline");
    }
}
