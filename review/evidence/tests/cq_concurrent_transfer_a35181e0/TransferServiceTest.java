import java.util.concurrent.*;

public final class TransferServiceTest {
    public static void main(String[] args) throws Exception {
        testBasicTransferAndInsufficientFunds();
        testSelfTransferAndDuplicateId();
        testOverflowIsAtomic();
        testConcurrentOppositeTransfersDoNotDeadlock();
        System.out.println("PASS");
    }

    private static void testBasicTransferAndInsufficientFunds() {
        TransferService.Account a = new TransferService.Account(1, 100);
        TransferService.Account b = new TransferService.Account(2, 50);

        assert TransferService.transfer(a, b, 30);
        assert a.balanceCents() == 70;
        assert b.balanceCents() == 80;

        assert !TransferService.transfer(a, b, 1000);
        assert a.balanceCents() == 70;
        assert b.balanceCents() == 80;
    }

    private static void testSelfTransferAndDuplicateId() {
        TransferService.Account a = new TransferService.Account(1, 100);
        assert TransferService.transfer(a, a, 10);
        assert a.balanceCents() == 100;

        TransferService.Account x = new TransferService.Account(7, 10);
        TransferService.Account y = new TransferService.Account(7, 20);
        boolean rejected = false;
        try {
            TransferService.transfer(x, y, 1);
        } catch (IllegalArgumentException expected) {
            rejected = true;
        }
        assert rejected;
        assert x.balanceCents() == 10;
        assert y.balanceCents() == 20;
    }

    private static void testOverflowIsAtomic() {
        TransferService.Account from = new TransferService.Account(1, 10);
        TransferService.Account to = new TransferService.Account(2, Long.MAX_VALUE);
        boolean overflow = false;
        try {
            TransferService.transfer(from, to, 1);
        } catch (ArithmeticException expected) {
            overflow = true;
        }
        assert overflow;
        assert from.balanceCents() == 10;
        assert to.balanceCents() == Long.MAX_VALUE;
    }

    private static void testConcurrentOppositeTransfersDoNotDeadlock() throws Exception {
        TransferService.Account a = new TransferService.Account(1, 100_000);
        TransferService.Account b = new TransferService.Account(2, 100_000);
        ExecutorService pool = Executors.newFixedThreadPool(2);
        CountDownLatch start = new CountDownLatch(1);

        Future<?> f1 = pool.submit(() -> {
            await(start);
            for (int i = 0; i < 10_000; i++) {
                if (!TransferService.transfer(a, b, 1)) {
                    throw new AssertionError("unexpected insufficient funds a->b");
                }
            }
        });
        Future<?> f2 = pool.submit(() -> {
            await(start);
            for (int i = 0; i < 10_000; i++) {
                if (!TransferService.transfer(b, a, 1)) {
                    throw new AssertionError("unexpected insufficient funds b->a");
                }
            }
        });

        start.countDown();
        try {
            f1.get(5, TimeUnit.SECONDS);
            f2.get(5, TimeUnit.SECONDS);
        } finally {
            pool.shutdownNow();
        }

        assert a.balanceCents() + b.balanceCents() == 200_000;
        assert a.balanceCents() == 100_000;
        assert b.balanceCents() == 100_000;
    }

    private static void await(CountDownLatch latch) {
        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new AssertionError(e);
        }
    }
}
