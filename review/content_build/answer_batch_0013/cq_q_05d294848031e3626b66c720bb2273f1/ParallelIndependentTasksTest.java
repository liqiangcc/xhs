import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public final class ParallelIndependentTasksTest {
    public static void main(String[] args) throws Exception {
        verifiesConcurrentStartAndJoin();
        verifiesExceptionalCompletion();
        verifiesNullGuards();
        System.out.println("PASS concurrent_start=3 join_completion=verified exceptional_completion=verified null_guards=verified");
    }

    private static void verifiesConcurrentStartAndJoin() throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);
        try {
            CountDownLatch started = new CountDownLatch(3);
            CountDownLatch release = new CountDownLatch(1);
            AtomicInteger completed = new AtomicInteger();

            Runnable task = () -> {
                started.countDown();
                await(release);
                completed.incrementAndGet();
            };

            CompletableFuture<Void> all =
                    ParallelIndependentTasks.runThree(pool, task, task, task);

            if (!started.await(2, TimeUnit.SECONDS)) {
                throw new AssertionError(
                        "all three tasks did not enter concurrently before release; executor/scheduling is effectively serial");
            }
            if (all.isDone()) {
                throw new AssertionError("allOf must not complete while tasks are still blocked");
            }

            release.countDown();
            all.get(2, TimeUnit.SECONDS);

            if (completed.get() != 3) {
                throw new AssertionError("expected all 3 tasks completed, actual=" + completed.get());
            }
        } finally {
            pool.shutdownNow();
            if (!pool.awaitTermination(2, TimeUnit.SECONDS)) {
                throw new AssertionError("executor failed to terminate");
            }
        }
    }

    private static void verifiesExceptionalCompletion() throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(3);
        try {
            CountDownLatch normalCompleted = new CountDownLatch(2);
            Runnable normal = normalCompleted::countDown;
            Runnable failing = () -> {
                throw new IllegalStateException("boom");
            };

            CompletableFuture<Void> all =
                    ParallelIndependentTasks.runThree(pool, normal, failing, normal);

            try {
                all.join();
                throw new AssertionError("expected exceptional completion");
            } catch (CompletionException expected) {
                if (!(expected.getCause() instanceof IllegalStateException)
                        || !"boom".equals(expected.getCause().getMessage())) {
                    throw new AssertionError("unexpected cause", expected);
                }
            }

            if (!normalCompleted.await(1, TimeUnit.SECONDS)) {
                throw new AssertionError("allOf should not prevent independent normal tasks from running");
            }
        } finally {
            pool.shutdownNow();
            pool.awaitTermination(2, TimeUnit.SECONDS);
        }
    }

    private static void verifiesNullGuards() {
        ExecutorService pool = Executors.newFixedThreadPool(3);
        try {
            Runnable noop = () -> {};
            expectNull(() -> ParallelIndependentTasks.runThree(null, noop, noop, noop));
            expectNull(() -> ParallelIndependentTasks.runThree(pool, null, noop, noop));
            expectNull(() -> ParallelIndependentTasks.runThree(pool, noop, null, noop));
            expectNull(() -> ParallelIndependentTasks.runThree(pool, noop, noop, null));
        } finally {
            pool.shutdownNow();
        }
    }

    private static void expectNull(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected NullPointerException");
        } catch (NullPointerException expected) {
            // expected
        }
    }

    private static void await(CountDownLatch latch) {
        boolean interrupted = false;
        while (true) {
            try {
                latch.await();
                break;
            } catch (InterruptedException e) {
                interrupted = true;
            }
        }
        if (interrupted) {
            Thread.currentThread().interrupt();
        }
    }
}
