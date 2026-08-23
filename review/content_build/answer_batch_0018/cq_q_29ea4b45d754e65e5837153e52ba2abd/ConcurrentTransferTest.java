import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

public final class ConcurrentTransferTest {
    private static int fixed;

    public static void main(String[] args) throws Exception {
        fixedCases();
        opposingTransfers();
        randomTransfers();
        System.out.println("PASS fixed=" + fixed
                + " opposingThreads=8 opposingOps=160000"
                + " randomThreads=12 randomOps=60000"
                + " conservation=true nonnegative=true progress=true");
    }

    private static void fixedCases() {
        ConcurrentTransfer.Account a = new ConcurrentTransfer.Account(1, 100);
        ConcurrentTransfer.Account b = new ConcurrentTransfer.Account(2, 20);
        require(ConcurrentTransfer.transfer(a, b, 30), "success should return true");
        require(a.balance() == 70 && b.balance() == 50, "success balances");
        fixed++;

        a = new ConcurrentTransfer.Account(1, 10);
        b = new ConcurrentTransfer.Account(2, 20);
        require(!ConcurrentTransfer.transfer(a, b, 11), "insufficient should return false");
        require(a.balance() == 10 && b.balance() == 20, "insufficient must not mutate");
        fixed++;

        a = new ConcurrentTransfer.Account(1, 10);
        require(ConcurrentTransfer.transfer(a, a, 9), "self transfer should succeed");
        require(a.balance() == 10, "self transfer must be no-op");
        fixed++;

        final ConcurrentTransfer.Account amountA = new ConcurrentTransfer.Account(1, 10);
        final ConcurrentTransfer.Account amountB = new ConcurrentTransfer.Account(2, 20);
        expect(IllegalArgumentException.class, () -> ConcurrentTransfer.transfer(amountA, amountB, 0));
        require(amountA.balance() == 10 && amountB.balance() == 20, "invalid amount must not mutate");
        fixed++;

        final ConcurrentTransfer.Account duplicateA = new ConcurrentTransfer.Account(7, 10);
        final ConcurrentTransfer.Account duplicateB = new ConcurrentTransfer.Account(7, 20);
        expect(IllegalArgumentException.class, () -> ConcurrentTransfer.transfer(duplicateA, duplicateB, 1));
        require(duplicateA.balance() == 10 && duplicateB.balance() == 20, "duplicate id must not mutate");
        fixed++;

        final ConcurrentTransfer.Account overflowA = new ConcurrentTransfer.Account(1, 10);
        final ConcurrentTransfer.Account overflowB = new ConcurrentTransfer.Account(2, Long.MAX_VALUE);
        expect(ArithmeticException.class, () -> ConcurrentTransfer.transfer(overflowA, overflowB, 1));
        require(overflowA.balance() == 10 && overflowB.balance() == Long.MAX_VALUE, "overflow must not partially mutate");
        fixed++;
    }

    private static void opposingTransfers() throws Exception {
        ConcurrentTransfer.Account a = new ConcurrentTransfer.Account(1, 1_000_000);
        ConcurrentTransfer.Account b = new ConcurrentTransfer.Account(2, 1_000_000);
        int threads = 8;
        int iterations = 20_000;
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        AtomicReference<Throwable> failure = new AtomicReference<>();

        for (int t = 0; t < threads; t++) {
            final boolean forward = (t % 2 == 0);
            Thread worker = new Thread(() -> {
                try {
                    start.await();
                    for (int i = 0; i < iterations; i++) {
                        boolean ok = forward
                                ? ConcurrentTransfer.transfer(a, b, 1)
                                : ConcurrentTransfer.transfer(b, a, 1);
                        require(ok, "opposing transfer unexpectedly failed");
                    }
                } catch (Throwable ex) {
                    failure.compareAndSet(null, ex);
                } finally {
                    done.countDown();
                }
            }, "opposing-" + t);
            worker.start();
        }

        start.countDown();
        require(done.await(20, TimeUnit.SECONDS), "opposing transfers did not make progress");
        if (failure.get() != null) {
            throw new AssertionError("opposing worker failed", failure.get());
        }
        require(a.balance() == 1_000_000 && b.balance() == 1_000_000,
                "balanced opposing transfers must restore exact balances");
    }

    private static void randomTransfers() throws Exception {
        int accountCount = 8;
        ConcurrentTransfer.Account[] accounts = new ConcurrentTransfer.Account[accountCount];
        long initial = 1_000_000;
        for (int i = 0; i < accountCount; i++) {
            accounts[i] = new ConcurrentTransfer.Account(i + 1, initial);
        }
        long expectedTotal = initial * accountCount;

        int threads = 12;
        int iterations = 5_000;
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        AtomicReference<Throwable> failure = new AtomicReference<>();
        List<Thread> workers = new ArrayList<>();

        for (int t = 0; t < threads; t++) {
            final int workerId = t;
            Thread worker = new Thread(() -> {
                try {
                    Random random = new Random(20260823L + workerId * 104729L);
                    start.await();
                    for (int i = 0; i < iterations; i++) {
                        int fromIndex = random.nextInt(accountCount);
                        int toIndex;
                        do {
                            toIndex = random.nextInt(accountCount);
                        } while (toIndex == fromIndex);
                        long amount = random.nextInt(100) + 1L;
                        ConcurrentTransfer.transfer(accounts[fromIndex], accounts[toIndex], amount);
                    }
                } catch (Throwable ex) {
                    failure.compareAndSet(null, ex);
                } finally {
                    done.countDown();
                }
            }, "random-" + t);
            workers.add(worker);
            worker.start();
        }

        start.countDown();
        require(done.await(20, TimeUnit.SECONDS), "random transfers did not make progress");
        if (failure.get() != null) {
            throw new AssertionError("random worker failed", failure.get());
        }

        long total = 0;
        for (ConcurrentTransfer.Account account : accounts) {
            long balance = account.balance();
            require(balance >= 0, "negative balance");
            total = Math.addExact(total, balance);
        }
        require(total == expectedTotal, "total balance must be conserved");
    }

    private static void expect(Class<? extends Throwable> type, ThrowingRunnable action) {
        try {
            action.run();
            throw new AssertionError("expected " + type.getSimpleName());
        } catch (Throwable ex) {
            if (!type.isInstance(ex)) {
                throw new AssertionError("expected " + type.getSimpleName() + " but got " + ex, ex);
            }
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    @FunctionalInterface
    private interface ThrowingRunnable {
        void run() throws Exception;
    }
}
