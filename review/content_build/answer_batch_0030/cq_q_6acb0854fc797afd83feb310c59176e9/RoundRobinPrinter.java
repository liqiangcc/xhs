import java.util.function.BiConsumer;

public final class RoundRobinPrinter {
    private final Object monitor = new Object();
    private final int workerCount;
    private final int maxValue;
    private int next = 1;

    public RoundRobinPrinter(int workerCount, int maxValue) {
        if (workerCount < 2) {
            throw new IllegalArgumentException("workerCount must be >= 2");
        }
        if (maxValue < 0) {
            throw new IllegalArgumentException("maxValue must be >= 0");
        }
        this.workerCount = workerCount;
        this.maxValue = maxValue;
    }

    public void runWorker(int workerId, BiConsumer<Integer, Integer> sink) throws InterruptedException {
        if (workerId < 0 || workerId >= workerCount) {
            throw new IllegalArgumentException("invalid workerId");
        }
        while (true) {
            synchronized (monitor) {
                while (next <= maxValue && ownerFor(next) != workerId) {
                    monitor.wait();
                }
                if (next > maxValue) {
                    return;
                }
                int value = next++;
                sink.accept(workerId, value);
                monitor.notifyAll();
            }
        }
    }

    private int ownerFor(int value) {
        return (value - 1) % workerCount;
    }
}
