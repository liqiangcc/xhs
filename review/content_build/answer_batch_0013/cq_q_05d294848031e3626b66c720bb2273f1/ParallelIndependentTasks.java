import java.util.Objects;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;

public final class ParallelIndependentTasks {
    private ParallelIndependentTasks() {}

    public static CompletableFuture<Void> runThree(
            Executor executor,
            Runnable a,
            Runnable b,
            Runnable c) {
        Objects.requireNonNull(executor, "executor");
        Objects.requireNonNull(a, "a");
        Objects.requireNonNull(b, "b");
        Objects.requireNonNull(c, "c");

        CompletableFuture<Void> fa = CompletableFuture.runAsync(a, executor);
        CompletableFuture<Void> fb = CompletableFuture.runAsync(b, executor);
        CompletableFuture<Void> fc = CompletableFuture.runAsync(c, executor);
        return CompletableFuture.allOf(fa, fb, fc);
    }
}
